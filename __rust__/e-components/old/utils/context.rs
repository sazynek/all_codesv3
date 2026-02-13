//! Optimized animation context with efficient repaint management and statistics

use egui::Context;
use std::cell::RefCell;
use std::collections::HashSet;
use std::hash::BuildHasherDefault;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{Duration, Instant};

// Use faster hasher for performance
type FastHashSet<K> = HashSet<K, BuildHasherDefault<fxhash::FxHasher>>;

thread_local! {
    static GLOBAL_CTX: RefCell<Option<Context>> = RefCell::new(None);
    static ACTIVE_ANIMATIONS: RefCell<FastHashSet<String>> = RefCell::new(FastHashSet::default());
    static LAST_REPAINT_TIME: RefCell<Option<Instant>> = RefCell::new(None);
}

// Atomic counters for lock-free statistics
static TOTAL_REPAINTS: AtomicU64 = AtomicU64::new(0);
static ANIMATION_UPDATES: AtomicU64 = AtomicU64::new(0);
// static LAST_FRAME_TIME: AtomicU64 = AtomicU64::new(0);

/// Global animation context management
pub struct AnimationContext;

impl AnimationContext {
    /// Initialize global context - must be called before any animations
    pub fn init(ctx: &Context) {
        GLOBAL_CTX.with(|global_ctx| {
            *global_ctx.borrow_mut() = Some(ctx.clone());
        });
    }
    
    /// Execute function with animation context, handling repaint requests
    pub fn with_context<F, R>(f: F) -> R
    where
        F: FnOnce(&Context) -> R,
    {
        GLOBAL_CTX.with(|ctx| {
            let ctx_borrow = ctx.borrow();
            let ctx_ref = ctx_borrow.as_ref().expect("AnimationContext not initialized");
            let result = f(ctx_ref);
            
            // Request repaint only if there are active animations
            if Self::has_active_animations() {
                Self::request_optimized_repaint(ctx_ref);
            }
            
            result
        })
    }

    /// Register animation as active
    #[inline]
    pub fn register_active_animation(id: String) {
        ACTIVE_ANIMATIONS.with(|animations| {
            animations.borrow_mut().insert(id);
        });
    }

    /// Remove animation from active set
    #[inline]
    pub fn unregister_active_animation(id: &str) {
        ACTIVE_ANIMATIONS.with(|animations| {
            animations.borrow_mut().remove(id);
        });
    }

    /// Check if any animations are currently active
    #[inline]
    pub fn has_active_animations() -> bool {
        ACTIVE_ANIMATIONS.with(|animations| {
            !animations.borrow().is_empty()
        })
    }

    /// Get global context for external use
    pub fn get_global_context() -> Option<Context> {
        GLOBAL_CTX.with(|ctx| {
            ctx.borrow().clone()
        })
    }

    /// Clear all active animations (e.g., on scene change)
    pub fn clear_active_animations() {
        ACTIVE_ANIMATIONS.with(|animations| {
            animations.borrow_mut().clear();
        });
    }

    /// Force immediate repaint ignoring optimizations
    pub fn force_repaint() {
        if let Some(ctx) = Self::get_global_context() {
            ctx.request_repaint();
            LAST_REPAINT_TIME.with(|last_repaint| {
                *last_repaint.borrow_mut() = Some(Instant::now());
            });
            TOTAL_REPAINTS.fetch_add(1, Ordering::Relaxed);
        }
    }

    // Internal optimized repaint logic
    fn request_optimized_repaint(ctx: &Context) {
        let now = Instant::now();
        let should_repaint = LAST_REPAINT_TIME.with(|last_repaint| {
            let mut last = last_repaint.borrow_mut();
            match *last {
                Some(last_time) => {
                    // Limit to ~60 FPS for animation updates
                    let should = now.duration_since(last_time).as_millis() >= 16;
                    if should {
                        *last = Some(now);
                    }
                    should
                }
                None => {
                    *last = Some(now);
                    true
                }
            }
        });
        
        if should_repaint {
            ctx.request_repaint();
            TOTAL_REPAINTS.fetch_add(1, Ordering::Relaxed);
        }
    }
}

// ============================ REPAINT MANAGER ============================

use std::sync::Mutex;
use once_cell::sync::Lazy;

/// Thread-safe repaint statistics with circular buffer
static REPAINT_STATS: Lazy<Mutex<RepaintStats>> = Lazy::new(|| {
    Mutex::new(RepaintStats::new())
});

/// Efficient statistics tracking with circular buffer
#[derive(Debug)]
struct RepaintStats {
    repaint_intervals: [Duration; 100], // Circular buffer
    count: usize,
    index: usize,
    last_repaint: Option<Instant>,
}

impl RepaintStats {
    fn new() -> Self {
        Self {
            repaint_intervals: [Duration::ZERO; 100],
            count: 0,
            index: 0,
            last_repaint: None,
        }
    }

    /// Record repaint with circular buffer
    fn record_repaint(&mut self) {
        let now = Instant::now();
        
        if let Some(last) = self.last_repaint {
            let interval = now.duration_since(last);
            
            // Circular buffer implementation
            self.repaint_intervals[self.index] = interval;
            self.index = (self.index + 1) % self.repaint_intervals.len();
            self.count = self.count.saturating_add(1).min(self.repaint_intervals.len());
        }
        
        self.last_repaint = Some(now);
    }

    /// Calculate statistics efficiently
    fn get_stats(&self) -> RepaintStatistics {
        let (total_repaints, animation_updates, avg_interval) = if self.count > 0 {
            let sum: Duration = self.repaint_intervals[..self.count].iter().sum();
            let avg = sum / self.count as u32;
            (
                TOTAL_REPAINTS.load(Ordering::Relaxed),
                ANIMATION_UPDATES.load(Ordering::Relaxed),
                avg,
            )
        } else {
            (0, 0, Duration::ZERO)
        };

        RepaintStatistics {
            total_repaints,
            average_interval: avg_interval,
            animation_updates,
        }
    }
}

/// Public statistics structure
#[derive(Debug, Clone, Copy)]
pub struct RepaintStatistics {
    pub total_repaints: u64,
    pub average_interval: Duration,
    pub animation_updates: u64,
}

/// High-performance repaint management
pub struct RepaintManager;

impl RepaintManager {
    /// Record repaint with atomic counter
    #[inline]
    pub fn record_repaint() {
        if let Ok(mut stats) = REPAINT_STATS.lock() {
            stats.record_repaint();
        }
    }

    /// Record animation update with atomic counter
    #[inline]
    pub fn record_animation_update() {
        ANIMATION_UPDATES.fetch_add(1, Ordering::Relaxed);
    }

    /// Get current statistics
    pub fn get_statistics() -> RepaintStatistics {
        if let Ok(stats) = REPAINT_STATS.lock() {
            stats.get_stats()
        } else {
            RepaintStatistics {
                total_repaints: 0,
                average_interval: Duration::ZERO,
                animation_updates: 0,
            }
        }
    }

    /// Smart repaint decision based on progress and FPS limits
    #[inline]
    pub fn should_repaint_based_on_progress(old_progress: f32, new_progress: f32, fps_limit: u32) -> bool {
        // Early exit if no change
        if (new_progress - old_progress).abs() < f32::EPSILON {
            return false;
        }

        // Adaptive repaint based on progress change and FPS limits
        let progress_diff = (new_progress - old_progress).abs();
        let min_progress_step = 1.0 / fps_limit as f32;
        
        progress_diff >= min_progress_step || new_progress >= 1.0 || new_progress <= 0.0
    }
}