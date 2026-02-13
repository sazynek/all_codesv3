// motion.rs
use crate::timeline::Timeline;
use crate::easing::Easing;

/// Базовый трейт для всех анимируемых свойств
pub trait Animatable: Clone {
    fn interpolate(&self, other: &Self, progress: f64) -> Self;
}

// Реализации для базовых типов
impl Animatable for f32 {
    fn interpolate(&self, other: &Self, progress: f64) -> Self {
        (*self as f64 + (*other as f64 - *self as f64) * progress) as f32
    }
}

impl Animatable for f64 {
    fn interpolate(&self, other: &Self, progress: f64) -> Self {
        self + (other - self) * progress
    }
}
impl Animatable for egui::Pos2 {
    fn interpolate(&self, other: &Self, progress: f64) -> Self {
        egui::Pos2 {
            x: self.x + (other.x - self.x) * progress as f32,
            y: self.y + (other.y - self.y) * progress as f32,
        }
    }
}
impl Animatable for egui::Color32 {
    fn interpolate(&self, other: &Self, progress: f64) -> Self {
        let r = (self.r() as f64).interpolate(&(other.r() as f64), progress) as u8;
        let g = (self.g() as f64).interpolate(&(other.g() as f64), progress) as u8;
        let b = (self.b() as f64).interpolate(&(other.b() as f64), progress) as u8;
        let a = (self.a() as f64).interpolate(&(other.a() as f64), progress) as u8;
        egui::Color32::from_rgba_premultiplied(r, g, b, a)
    }
}

impl Animatable for egui::Vec2 {
    fn interpolate(&self, other: &Self, progress: f64) -> Self {
        egui::Vec2 {
            x: self.x + (other.x - self.x) * progress as f32,
            y: self.y + (other.y - self.y) * progress as f32,
        }
    }
}

/// Основная структура анимации
#[derive(Clone)]
pub struct Motion<T: Animatable> {
    pub from: T,
    pub to: T,
    pub duration: f64,
    pub delay: f64,
    pub easing: Easing,
    pub timeline: Timeline,
}

impl<T: Animatable> Motion<T> {
    pub fn new(from: T, to: T, duration: f64) -> Self {
        Self {
            from,
            to,
            duration,
            delay: 0.0,
            easing: Easing::Linear,
            timeline: Timeline::new(),
        }
    }

    pub fn with_delay(mut self, delay: f64) -> Self {
        self.delay = delay;
        self
    }

    pub fn with_easing(mut self, easing: Easing) -> Self {
        self.easing = easing;
        self
    }

    pub fn start(&mut self) {
        self.timeline.start();
    }

    pub fn value(&self) -> T {
        let elapsed = self.timeline.elapsed_seconds();
        
        if elapsed < self.delay {
            return self.from.clone();
        }

        let progress = (elapsed - self.delay) / self.duration;
        
        if progress >= 1.0 {
            return self.to.clone();
        }

        let eased_progress = self.easing.apply(progress);
        self.from.interpolate(&self.to, eased_progress)
    }

    pub fn is_finished(&self) -> bool {
        self.timeline.elapsed_seconds() >= self.duration + self.delay
    }

    pub fn is_running(&self) -> bool {
        !self.is_finished() && self.timeline.elapsed_seconds() >= self.delay
    }

    pub fn progress(&self) -> f64 {
        let elapsed = self.timeline.elapsed_seconds();
        
        if elapsed < self.delay {
            return 0.0;
        }

        let progress = (elapsed - self.delay) / self.duration;
        progress.min(1.0)
    }
}