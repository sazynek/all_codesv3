use std::f32::consts::PI;

/// Типы easing-функций для плавности анимации
pub type EasingFn = fn(f32) -> f32;

// Предварительно вычисленные константы для оптимизации
const C1: f32 = 1.70158;
const C2: f32 = C1 * 1.525;
const C3: f32 = C1 + 1.0;
const N1: f32 = 7.5625;
const D1: f32 = 2.75;

/// Базовые easing-функции
pub const LINEAR: EasingFn = |t| t;

#[inline]
pub const fn ease_in_quad(t: f32) -> f32 {
    t * t
}

#[inline]
pub const fn ease_out_quad(t: f32) -> f32 {
    1.0 - (1.0 - t) * (1.0 - t)
}

#[inline]
pub fn ease_in_out_quad(t: f32) -> f32 {
    if t < 0.5 {
        2.0 * t * t
    } else {
        1.0 - (-2.0 * t + 2.0).mul_add(-2.0 * t + 2.0, 0.0) / 2.0
    }
}

/// Кубические easing-функции
#[inline]
pub const fn ease_in_cubic(t: f32) -> f32 {
    t * t * t
}

#[inline]
pub fn ease_out_cubic(t: f32) -> f32 {
    1.0 - (1.0 - t).powi(3)
}

#[inline]
pub fn ease_in_out_cubic(t: f32) -> f32 {
    if t < 0.5 {
        4.0 * t * t * t
    } else {
        1.0 - (-2.0 * t + 2.0).powi(3) / 2.0
    }
}

/// Квартические easing-функции
#[inline]
pub const fn ease_in_quart(t: f32) -> f32 {
    t * t * t * t
}

#[inline]
pub fn ease_out_quart(t: f32) -> f32 {
    1.0 - (1.0 - t).powi(4)
}

#[inline]
pub fn ease_in_out_quart(t: f32) -> f32 {
    if t < 0.5 {
        8.0 * t * t * t * t
    } else {
        1.0 - (-2.0 * t + 2.0).powi(4) / 2.0
    }
}

/// Синусоидальные easing-функции
#[inline]
pub fn ease_in_sine(t: f32) -> f32 {
    1.0 - (t * PI / 2.0).cos()
}

#[inline]
pub fn ease_out_sine(t: f32) -> f32 {
    (t * PI / 2.0).sin()
}

#[inline]
pub fn ease_in_out_sine(t: f32) -> f32 {
    -((PI * t).cos() - 1.0) / 2.0
}

/// Экспоненциальные easing-функции
#[inline]
pub fn ease_in_expo(t: f32) -> f32 {
    if t == 0.0 {
        0.0
    } else {
        2.0f32.powf(10.0 * t - 10.0)
    }
}

#[inline]
pub fn ease_out_expo(t: f32) -> f32 {
    if t == 1.0 {
        1.0
    } else {
        1.0 - 2.0f32.powf(-10.0 * t)
    }
}

#[inline]
pub fn ease_in_out_expo(t: f32) -> f32 {
    if t == 0.0 || t == 1.0 {
        t
    } else if t < 0.5 {
        2.0f32.powf(20.0 * t - 10.0) / 2.0
    } else {
        (2.0 - 2.0f32.powf(-20.0 * t + 10.0)) / 2.0
    }
}

/// Упругие easing-функции
#[inline]
pub fn ease_in_elastic(t: f32) -> f32 {
    if t == 0.0 || t == 1.0 {
        t
    } else {
        -2.0f32.powf(10.0 * t - 10.0) * ((t * 10.0 - 10.75) * (2.0 * PI) / 3.0).sin()
    }
}

#[inline]
pub fn ease_out_elastic(t: f32) -> f32 {
    if t == 0.0 || t == 1.0 {
        t
    } else {
        2.0f32.powf(-10.0 * t) * ((t * 10.0 - 0.75) * (2.0 * PI) / 3.0).sin() + 1.0
    }
}

#[inline]
pub fn ease_in_out_elastic(t: f32) -> f32 {
    if t == 0.0 || t == 1.0 {
        t
    } else if t < 0.5 {
        -(2.0f32.powf(20.0 * t - 10.0) * ((20.0 * t - 11.125) * (2.0 * PI) / 4.5).sin()) / 2.0
    } else {
        (2.0f32.powf(-20.0 * t + 10.0) * ((20.0 * t - 11.125) * (2.0 * PI) / 4.5).sin()) / 2.0 + 1.0
    }
}

/// Вспомогательная функция для bounce easing
#[inline]
fn ease_out_bounce(t: f32) -> f32 {
    if t < 1.0 / D1 {
        N1 * t * t
    } else if t < 2.0 / D1 {
        let t = t - 1.5 / D1;
        N1 * t * t + 0.75
    } else if t < 2.5 / D1 {
        let t = t - 2.25 / D1;
        N1 * t * t + 0.9375
    } else {
        let t = t - 2.625 / D1;
        N1 * t * t + 0.984375
    }
}

/// Отскакивающие easing-функции
#[inline]
pub fn ease_in_bounce(t: f32) -> f32 {
    1.0 - ease_out_bounce(1.0 - t)
}

#[inline]
pub fn ease_out_bounce_wrapper(t: f32) -> f32 {
    ease_out_bounce(t)
}

#[inline]
pub fn ease_in_out_bounce(t: f32) -> f32 {
    if t < 0.5 {
        (1.0 - ease_out_bounce(1.0 - 2.0 * t)) / 2.0
    } else {
        (1.0 + ease_out_bounce(2.0 * t - 1.0)) / 2.0
    }
}

/// Back easing-функции
#[inline]
pub fn ease_in_back(t: f32) -> f32 {
    C3 * t * t * t - C1 * t * t
}

#[inline]
pub fn ease_out_back(t: f32) -> f32 {
    1.0 + C3 * (t - 1.0).powi(3) + C1 * (t - 1.0).powi(2)
}

#[inline]
pub fn ease_in_out_back(t: f32) -> f32 {
    if t < 0.5 {
        ((2.0 * t).powi(2) * ((C2 + 1.0) * 2.0 * t - C2)) / 2.0
    } else {
        ((2.0 * t - 2.0).powi(2) * ((C2 + 1.0) * (t * 2.0 - 2.0) + C2) + 2.0) / 2.0
    }
}

// Псевдонимы для обратной совместимости
pub const EASE_IN: EasingFn = ease_in_quad;
pub const EASE_OUT: EasingFn = ease_out_quad;
pub const EASE_IN_OUT: EasingFn = ease_in_out_quad;
pub const EASE_IN_CUBIC: EasingFn = ease_in_cubic;
pub const EASE_OUT_CUBIC: EasingFn = ease_out_cubic;
pub const EASE_IN_OUT_CUBIC: EasingFn = ease_in_out_cubic;
pub const EASE_IN_QUART: EasingFn = ease_in_quart;
pub const EASE_OUT_QUART: EasingFn = ease_out_quart;
pub const EASE_IN_OUT_QUART: EasingFn = ease_in_out_quart;
pub const EASE_IN_SINE: EasingFn = ease_in_sine;
pub const EASE_OUT_SINE: EasingFn = ease_out_sine;
pub const EASE_IN_OUT_SINE: EasingFn = ease_in_out_sine;
pub const EASE_IN_EXPO: EasingFn = ease_in_expo;
pub const EASE_OUT_EXPO: EasingFn = ease_out_expo;
pub const EASE_IN_OUT_EXPO: EasingFn = ease_in_out_expo;
pub const EASE_IN_ELASTIC: EasingFn = ease_in_elastic;
pub const EASE_OUT_ELASTIC: EasingFn = ease_out_elastic;
pub const EASE_IN_OUT_ELASTIC: EasingFn = ease_in_out_elastic;
pub const EASE_IN_BOUNCE: EasingFn = ease_in_bounce;
pub const EASE_OUT_BOUNCE: EasingFn = ease_out_bounce_wrapper;
pub const EASE_IN_OUT_BOUNCE: EasingFn = ease_in_out_bounce;
pub const EASE_IN_BACK: EasingFn = ease_in_back;
pub const EASE_OUT_BACK: EasingFn = ease_out_back;
pub const EASE_IN_OUT_BACK: EasingFn = ease_in_out_back;