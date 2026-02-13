//! High-performance animation system with optimized memory usage

mod utils;
pub mod preset;

use std::cell::RefCell;
use std::collections::HashMap;
use std::hash::BuildHasherDefault;
use std::rc::Rc;
use std::time::{Duration, Instant};
pub use crate::utils::context;
use crate::utils::context::RepaintManager;
pub use crate::utils::easing;

// Use faster hasher for better performance
type FastHashMap<K, V> = HashMap<K, V, BuildHasherDefault<fxhash::FxHasher>>;

/// Trait for types that can be interpolated between two values
pub trait Interpolate: Copy + Clone {
    fn interpolate(start: Self, end: Self, progress: f32) -> Self;
}

/// Optimized animation manager with fast lookups
#[derive(Clone,Debug)]
pub struct AnimationManager {
    active_animations: Rc<RefCell<FastHashMap<String, Instant>>>,
}

impl AnimationManager {
    pub fn new() -> Self {
        Self {
            active_animations: Rc::new(RefCell::new(FastHashMap::default())),
        }
    }

    /// Register animation as active and request repaint
    #[inline]
    pub fn register_active(&self, id: String) {
        self.active_animations.borrow_mut().insert(id.clone(), Instant::now());
        context::AnimationContext::register_active_animation(id);
    }

    /// Remove animation from active set
    #[inline]
    pub fn unregister_active(&self, id: &str) {
        self.active_animations.borrow_mut().remove(id);
        context::AnimationContext::unregister_active_animation(id);
    }

    /// Clean up animations that haven't been updated within timeout
    pub fn cleanup_stale_animations(&self, timeout: Duration) {
        let now = Instant::now();
        self.active_animations.borrow_mut().retain(|id, time| {
            if now.duration_since(*time) > timeout {
                context::AnimationContext::unregister_active_animation(id);
                false
            } else {
                true
            }
        });
    }
}

/// State machine for animation lifecycle
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AnimationState {
    Playing,
    Completed,
    Stopped,
    Unactive,
}

/// User interaction types that trigger animations
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Interaction {
    HoverStart,
    HoverEnd,
    ClickStart,
    ClickStop,
    Toggle,
}

/// Current state of UI element interaction
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum InteractionState {
    Idle,
    Hovered,
    Clicked,
}

// ============================ OPTIMIZED ANIMATION STRUCTURES ============================

/// Compact animation instance data
#[derive(Clone,Debug)]
struct AnimationInstanceData<T: Interpolate> {
    start_value: T,
    end_value: T,
    current_value: T,
    current_progress: f32,
    start_time: Option<Instant>,
}

/// Individual animation instance with optimized memory layout
#[derive(Clone,Debug)]
struct AnimationInstance<T: Interpolate> {
    data: AnimationInstanceData<T>,
    state: AnimationState,
    interaction_state: InteractionState,
    pre_hover_state: Option<InteractionState>,
    is_toggled: bool,
}

/// Immutable template data shared between instances
#[derive(Clone, Debug)]
struct AnimationTemplateData<T: Interpolate> {
    initial_start: T,
    initial_end: T,
    duration: Duration,
    easing: easing::EasingFn,
}

/// Main public interface for creating and managing animations
#[derive(Clone,Debug)]
pub struct AnimationTemplate<T: Interpolate> {
    template: Rc<AnimationTemplateData<T>>,
    instances: RefCell<FastHashMap<String, AnimationInstance<T>>>,
    manager: AnimationManager,
}

impl<T: Interpolate> AnimationTemplate<T> {
    /// Create new animation template with start/end values and duration
    pub fn new(initial_start: T, initial_end: T, duration: Duration) -> Self {
        Self {
            template: Rc::new(AnimationTemplateData {
                initial_start,
                initial_end,
                duration,
                easing: easing::LINEAR,
            }),
            instances: RefCell::new(FastHashMap::default()),
            manager: AnimationManager::new(),
        }
    }

    /// Set custom easing function for the animation
    pub fn with_easing(mut self, easing: easing::EasingFn) -> Self {
        self.template = Rc::new(AnimationTemplateData {
            easing,
            ..(*self.template).clone()
        });
        self
    }

    /// MAIN PUBLIC API - Get current animated value, updating if necessary
    pub fn animate(&self, id: impl Into<String>) -> T {
        let id = id.into();
        
        // Fast path: check existing instance first without mutable borrow
        if let Some(instance) = self.instances.borrow().get(&id) {
            // Fast exit for completed animations
            if instance.state == AnimationState::Completed && instance.data.current_progress >= 1.0 {
                return instance.data.current_value;
            }
        }

        RepaintManager::record_animation_update();
        context::AnimationContext::with_context(|ctx| {
            let mut instances = self.instances.borrow_mut();
            let instance = instances
                .entry(id.clone())
                .or_insert_with(|| self.create_instance());
            
            instance.update(ctx, &self.template, &id)
        })
    }
    
    /// Start reverse animation to initial start value
    pub fn stop(&self, id: impl Into<String>) {
        let id = id.into();
        let mut instances = self.instances.borrow_mut();
        
        if let Some(instance) = instances.get_mut(&id) {
            let current_value = instance.data.current_value;
            let initial_start = self.template.initial_start;
            
            instance.data = AnimationInstanceData {
                start_value: current_value,
                end_value: initial_start,
                current_value,
                current_progress: 0.0,
                start_time: Some(Instant::now()),
            };
            instance.state = AnimationState::Playing;
            instance.interaction_state = InteractionState::Idle;
            instance.is_toggled = false;
            
            self.manager.register_active(id);
        }
    }

    /// Start forward animation to initial end value  
    pub fn start(&self, id: impl Into<String>) {
        let id = id.into();
        let mut instances = self.instances.borrow_mut();
        
        if let Some(instance) = instances.get_mut(&id) {
            let current_value = instance.data.current_value;
            let initial_end = self.template.initial_end;
            
            instance.data = AnimationInstanceData {
                start_value: current_value,
                end_value: initial_end,
                current_value,
                current_progress: 0.0,
                start_time: Some(Instant::now()),
            };
            instance.state = AnimationState::Playing;
            instance.interaction_state = InteractionState::Clicked;
            instance.is_toggled = true;
            
            self.manager.register_active(id);
        }
    }

    /// Get current animation state
    pub fn get_state(&self, id: &str) -> AnimationState {
        self.instances.borrow()
            .get(id)
            .map(|inst| inst.state)
            .unwrap_or(AnimationState::Unactive)
    }

    /// Handle user interactions and trigger appropriate animations
    pub fn handle_interaction(&self, id: &str, interaction: Interaction) {
        let mut instances = self.instances.borrow_mut();
        
        if let Some(instance) = instances.get_mut(id) {
            let current_value = instance.data.current_value;
            
            match interaction {
                Interaction::HoverStart => {
                    if instance.interaction_state != InteractionState::Hovered {
                        instance.pre_hover_state = Some(instance.interaction_state);
                        instance.interaction_state = InteractionState::Hovered;
                        
                        instance.data = AnimationInstanceData {
                            start_value: current_value,
                            end_value: self.template.initial_end,
                            current_value,
                            current_progress: 0.0,
                            start_time: Some(Instant::now()),
                        };
                        instance.state = AnimationState::Playing;
                        
                        self.manager.register_active(id.to_string());
                    }
                }
                Interaction::HoverEnd => {
                    if instance.interaction_state == InteractionState::Hovered {
                        let previous_state = instance.pre_hover_state.unwrap_or(InteractionState::Idle);
                        instance.interaction_state = previous_state;
                        
                        let target_value = match previous_state {
                            InteractionState::Clicked => self.template.initial_end,
                            _ => self.template.initial_start,
                        };
                        
                        instance.data = AnimationInstanceData {
                            start_value: current_value,
                            end_value: target_value,
                            current_value,
                            current_progress: 0.0,
                            start_time: Some(Instant::now()),
                        };
                        instance.state = AnimationState::Playing;
                        instance.pre_hover_state = None;
                        
                        self.manager.register_active(id.to_string());
                    }
                }
                Interaction::ClickStart => {
                    instance.interaction_state = InteractionState::Clicked;
                    
                    instance.data = AnimationInstanceData {
                        start_value: current_value,
                        end_value: self.template.initial_end,
                        current_value,
                        current_progress: 0.0,
                        start_time: Some(Instant::now()),
                    };
                    instance.state = AnimationState::Playing;
                    instance.is_toggled = true;
                    
                    self.manager.register_active(id.to_string());
                }
                Interaction::ClickStop => {
                    instance.interaction_state = InteractionState::Idle;
                    
                    instance.data = AnimationInstanceData {
                        start_value: current_value,
                        end_value: self.template.initial_start,
                        current_value,
                        current_progress: 0.0,
                        start_time: Some(Instant::now()),
                    };
                    instance.state = AnimationState::Playing;
                    instance.is_toggled = false;
                    
                    self.manager.register_active(id.to_string());
                }
                Interaction::Toggle => {
                    instance.is_toggled = !instance.is_toggled;
                    
                    let (target_value, interaction_state) = if instance.is_toggled {
                        (self.template.initial_end, InteractionState::Clicked)
                    } else {
                        (self.template.initial_start, InteractionState::Idle)
                    };
                    
                    instance.data = AnimationInstanceData {
                        start_value: current_value,
                        end_value: target_value,
                        current_value,
                        current_progress: 0.0,
                        start_time: Some(Instant::now()),
                    };
                    instance.state = AnimationState::Playing;
                    instance.interaction_state = interaction_state;
                    
                    self.manager.register_active(id.to_string());
                }
            }
        }
    }

    /// Get current interaction state
    pub fn get_interaction_state(&self, id: &str) -> InteractionState {
        self.instances.borrow()
            .get(id)
            .map(|inst| inst.interaction_state)
            .unwrap_or(InteractionState::Idle)
    }

    /// Get current toggle state
    pub fn get_toggle_state(&self, id: &str) -> bool {
        self.instances.borrow()
            .get(id)
            .map(|inst| inst.is_toggled)
            .unwrap_or(false)
    }

    // Internal instance creation with optimized layout
    fn create_instance(&self) -> AnimationInstance<T> {
        AnimationInstance {
            data: AnimationInstanceData {
                start_value: self.template.initial_start,
                end_value: self.template.initial_end,
                current_value: self.template.initial_start,
                current_progress: 0.0,
                start_time: None,
            },
            state: AnimationState::Unactive,
            interaction_state: InteractionState::Idle,
            pre_hover_state: None,
            is_toggled: false,
        }
    }

    /// Clean up stale animations (1 minute timeout)
    pub fn cleanup_stale_animations(&self) {
        self.manager.cleanup_stale_animations(Duration::from_secs(60));
    }

    /// Get repaint statistics for performance monitoring
    pub fn get_repaint_statistics() -> crate::utils::context::RepaintStatistics {
        RepaintManager::get_statistics()
    }
}

impl<T: Interpolate> AnimationInstance<T> {
    /// Optimized animation update with minimal branching
    fn update(&mut self, ctx: &egui::Context, template: &AnimationTemplateData<T>, id: &str) -> T {
        // Fast exit for completed animations
        if self.state == AnimationState::Completed && self.data.current_progress >= 1.0 {
            return self.data.current_value;
        }

        if let Some(start_time) = self.data.start_time {
            let elapsed = Instant::now().duration_since(start_time);
            let progress = (elapsed.as_secs_f32() / template.duration.as_secs_f32()).min(1.0);
            
            let state_changed = if progress >= 1.0 {
                if self.state != AnimationState::Completed {
                    self.state = AnimationState::Completed;
                    context::AnimationContext::unregister_active_animation(id);
                    true
                } else {
                    false
                }
            } else if self.state == AnimationState::Completed {
                // Resume animation if progress reset
                self.state = AnimationState::Playing;
                true
            } else {
                false
            };

            self.data.current_progress = progress;
            let eased_progress = (template.easing)(progress);
            self.data.current_value = T::interpolate(self.data.start_value, self.data.end_value, eased_progress);

            // Always register active animation if playing
            if self.state == AnimationState::Playing {
                context::AnimationContext::register_active_animation(id.to_string());
            }

            // Request repaint on state change or if animation is active
            if state_changed || self.state == AnimationState::Playing {
                ctx.request_repaint();
            }
        } else if self.state == AnimationState::Playing {
            // Fix missing start_time for playing animations
            self.data.start_time = Some(Instant::now());
            ctx.request_repaint();
        }

        self.data.current_value
    }
}

// ============================ OPTIMIZED TYPE IMPLEMENTATIONS ============================

// Efficient implementations for common types
impl Interpolate for f32 {
    #[inline]
    fn interpolate(start: Self, end: Self, progress: f32) -> Self {
        start + (end - start) * progress
    }
}

impl Interpolate for f64 {
    #[inline]
    fn interpolate(start: Self, end: Self, progress: f32) -> Self {
        start + (end - start) * progress as f64
    }
}

impl Interpolate for i32 {
    #[inline]
    fn interpolate(start: Self, end: Self, progress: f32) -> Self {
        start + ((end - start) as f32 * progress) as i32
    }
}

/// Optimized 2D vector for position/size animations
#[derive(Debug, Clone, Copy, Default)]
pub struct Vec2 {
    pub x: f32,
    pub y: f32,
}

impl Interpolate for Vec2 {
    #[inline]
    fn interpolate(start: Self, end: Self, progress: f32) -> Self {
        Self {
            x: f32::interpolate(start.x, end.x, progress),
            y: f32::interpolate(start.y, end.y, progress),
        }
    }
}

impl Vec2 {
    #[inline]
    pub const fn new(x: f32, y: f32) -> Self {
        Self { x, y }
    }
}