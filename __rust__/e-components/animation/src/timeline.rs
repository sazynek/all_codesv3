// timeline.rs
use std::time::{Duration, Instant};

#[derive(Clone)]
pub struct Timeline {
    start_time: Option<Instant>,
    pause_duration: Duration,
    is_paused: bool,
}

impl Timeline {
    pub fn new() -> Self {
        Self {
            start_time: None,
            pause_duration: Duration::ZERO,
            is_paused: false,
        }
    }

    pub fn start(&mut self) {
        self.start_time = Some(Instant::now());
        self.pause_duration = Duration::ZERO;
        self.is_paused = false;
    }

    pub fn pause(&mut self) {
        if !self.is_paused && self.start_time.is_some() {
            self.is_paused = true;
            self.pause_duration = self.elapsed();
        }
    }

    pub fn resume(&mut self) {
        if self.is_paused {
            self.is_paused = false;
            self.start_time = Some(Instant::now() - self.pause_duration);
        }
    }

    pub fn elapsed(&self) -> Duration {
        if let Some(start) = self.start_time {
            if self.is_paused {
                self.pause_duration
            } else {
                start.elapsed() - self.pause_duration
            }
        } else {
            Duration::ZERO
        }
    }

    pub fn elapsed_seconds(&self) -> f64 {
        self.elapsed().as_secs_f64()
    }

    pub fn reset(&mut self) {
        self.start_time = None;
        self.pause_duration = Duration::ZERO;
        self.is_paused = false;
    }
}

impl Default for Timeline {
    fn default() -> Self {
        Self::new()
    }
}