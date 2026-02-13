// ==================== БАЗОВЫЕ АНИМАЦИИ ====================

#[macro_export]
macro_rules! fade {
    () => {
        (0.0, 1.0, std::time::Duration::from_millis(800), $crate::easing::EASE_IN_OUT_CUBIC)
    };
    ($from:expr => $to:expr) => {
        ($from, $to, std::time::Duration::from_millis(800), $crate::easing::EASE_IN_OUT_CUBIC)
    };
    ($from:expr => $to:expr, $duration_ms:expr) => {
        ($from, $to, std::time::Duration::from_millis($duration_ms), $crate::easing::EASE_IN_OUT_CUBIC)
    };
}

#[macro_export]
macro_rules! fade_in {
    () => {
        (0.0, 1.0, std::time::Duration::from_millis(700), $crate::easing::EASE_OUT_CUBIC)
    };
    ($duration_ms:expr) => {
        (0.0, 1.0, std::time::Duration::from_millis($duration_ms), $crate::easing::EASE_OUT_CUBIC)
    };
}

#[macro_export]
macro_rules! fade_out {
    () => {
        (1.0, 0.0, std::time::Duration::from_millis(700), $crate::easing::EASE_IN_CUBIC)
    };
    ($duration_ms:expr) => {
        (1.0, 0.0, std::time::Duration::from_millis($duration_ms), $crate::easing::EASE_IN_CUBIC)
    };
}

// ==================== СЛАЙД-АНИМАЦИИ ====================

#[macro_export]
macro_rules! slide {
    ($from:expr => $to:expr) => {
        ($from, $to, std::time::Duration::from_millis(800), $crate::easing::EASE_OUT_QUART)
    };
    ($to:expr) => {
        (0.0, $to, std::time::Duration::from_millis(800), $crate::easing::EASE_OUT_QUART)
    };
    ($from:expr => $to:expr, $duration_ms:expr) => {
        ($from, $to, std::time::Duration::from_millis($duration_ms), $crate::easing::EASE_OUT_QUART)
    };
}

#[macro_export]
macro_rules! slide_in_right {
    ($distance:expr) => {
        (-$distance, 0.0, std::time::Duration::from_millis(800), $crate::easing::EASE_OUT_BACK)
    };
    ($distance:expr, $duration_ms:expr) => {
        (-$distance, 0.0, std::time::Duration::from_millis($duration_ms), $crate::easing::EASE_OUT_BACK)
    };
}

#[macro_export]
macro_rules! slide_out_right {
    ($distance:expr) => {
        (0.0, $distance, std::time::Duration::from_millis(800), $crate::easing::EASE_IN_BACK)
    };
    ($distance:expr, $duration_ms:expr) => {
        (0.0, $distance, std::time::Duration::from_millis($duration_ms), $crate::easing::EASE_IN_BACK)
    };
}

#[macro_export]
macro_rules! slide_in_left {
    ($distance:expr) => {
        ($distance, 0.0, std::time::Duration::from_millis(800), $crate::easing::EASE_OUT_BACK)
    };
    ($distance:expr, $duration_ms:expr) => {
        ($distance, 0.00, std::time::Duration::from_millis($duration_ms), $crate::easing::EASE_OUT_BACK)
    };
}

#[macro_export]
macro_rules! slide_out_left {
    ($distance:expr) => {
        (0.0, -$distance, std::time::Duration::from_millis(800), $crate::easing::EASE_IN_BACK)
    };
    ($distance:expr, $duration_ms:expr) => {
        (0.0, -$distance, std::time::Duration::from_millis($duration_ms), $crate::easing::EASE_IN_BACK)
    };
}

#[macro_export]
macro_rules! slide_in_up {
    ($distance:expr) => {
        ($distance, 0.0, std::time::Duration::from_millis(800), $crate::easing::EASE_OUT_BACK)
    };
    ($distance:expr, $duration_ms:expr) => {
        ($distance, 0.0, std::time::Duration::from_millis($duration_ms), $crate::easing::EASE_OUT_BACK)
    };
}

#[macro_export]
macro_rules! slide_in_down {
    ($distance:expr) => {
        (-$distance, 0.0, std::time::Duration::from_millis(800), $crate::easing::EASE_OUT_BACK)
    };
    ($distance:expr, $duration_ms:expr) => {
        (-$distance, 0.0, std::time::Duration::from_millis($duration_ms), $crate::easing::EASE_OUT_BACK)
    };
}

// ==================== МАСШТАБИРОВАНИЕ ====================

#[macro_export]
macro_rules! scale {
    ($from:expr => $to:expr) => {
        ($from, $to, std::time::Duration::from_millis(700), $crate::easing::EASE_OUT_ELASTIC)
    };
    ($to:expr) => {
        (1.0, $to, std::time::Duration::from_millis(700), $crate::easing::EASE_OUT_ELASTIC)
    };
    ($from:expr => $to:expr, $duration_ms:expr) => {
        ($from, $to, std::time::Duration::from_millis($duration_ms), $crate::easing::EASE_OUT_ELASTIC)
    };
}

#[macro_export]
macro_rules! scale_in {
    () => {
        (0.0, 1.0, std::time::Duration::from_millis(700), $crate::easing::EASE_OUT_BACK)
    };
    ($duration_ms:expr) => {
        (0.0, 1.0, std::time::Duration::from_millis($duration_ms), $crate::easing::EASE_OUT_BACK)
    };
}

#[macro_export]
macro_rules! scale_out {
    () => {
        (1.0, 0.0, std::time::Duration::from_millis(700), $crate::easing::EASE_IN_BACK)
    };
    ($duration_ms:expr) => {
        (1.0, 0.0, std::time::Duration::from_millis($duration_ms), $crate::easing::EASE_IN_BACK)
    };
}

#[macro_export]
macro_rules! zoom_in {
    ($factor:expr) => {
        (1.0, $factor, std::time::Duration::from_millis(600), $crate::easing::EASE_OUT_ELASTIC)
    };
    ($factor:expr, $duration_ms:expr) => {
        (1.0, $factor, std::time::Duration::from_millis($duration_ms), $crate::easing::EASE_OUT_ELASTIC)
    };
}

#[macro_export]
macro_rules! zoom_out {
    ($factor:expr) => {
        (1.0, $factor, std::time::Duration::from_millis(600), $crate::easing::EASE_OUT_BACK)
    };
    ($factor:expr, $duration_ms:expr) => {
        (1.0, $factor, std::time::Duration::from_millis($duration_ms), $crate::easing::EASE_OUT_BACK)
    };
}

// ==================== СПЕЦИАЛЬНЫЕ ЭФФЕКТЫ ====================

#[macro_export]
macro_rules! bounce {
    () => {
        (0.0, 1.0, std::time::Duration::from_millis(1000), $crate::easing::EASE_OUT_BOUNCE)
    };
    ($from:expr => $to:expr) => {
        ($from, $to, std::time::Duration::from_millis(1000), $crate::easing::EASE_OUT_BOUNCE)
    };
    ($from:expr => $to:expr, $duration_ms:expr) => {
        ($from, $to, std::time::Duration::from_millis($duration_ms), $crate::easing::EASE_OUT_BOUNCE)
    };
}

#[macro_export]
macro_rules! elastic {
    () => {
        (0.0, 1.0, std::time::Duration::from_millis(900), $crate::easing::EASE_OUT_ELASTIC)
    };
    ($from:expr => $to:expr) => {
        ($from, $to, std::time::Duration::from_millis(900), $crate::easing::EASE_OUT_ELASTIC)
    };
    ($from:expr => $to:expr, $duration_ms:expr) => {
        ($from, $to, std::time::Duration::from_millis($duration_ms), $crate::easing::EASE_OUT_ELASTIC)
    };
}

#[macro_export]
macro_rules! spring {
    () => {
        (0.0, 1.0, std::time::Duration::from_millis(1200), $crate::easing::EASE_OUT_ELASTIC)
    };
    ($from:expr => $to:expr) => {
        ($from, $to, std::time::Duration::from_millis(1200), $crate::easing::EASE_OUT_ELASTIC)
    };
}

#[macro_export]
macro_rules! wobble {
    () => {
        (0.0, 1.0, std::time::Duration::from_millis(800), $crate::easing::EASE_OUT_BOUNCE)
    };
}

// ==================== ИНТЕРАКТИВНЫЕ ЭЛЕМЕНТЫ ====================

#[macro_export]
macro_rules! button_hover {
    () => {
        (0.0, 1.0, std::time::Duration::from_millis(400), $crate::easing::EASE_OUT_CUBIC)
    };
    ($duration_ms:expr) => {
        (0.0, 1.0, std::time::Duration::from_millis($duration_ms), $crate::easing::EASE_OUT_CUBIC)
    };
}

#[macro_export]
macro_rules! button_press {
    () => {
        (1.0, 0.95, std::time::Duration::from_millis(200), $crate::easing::EASE_OUT_CUBIC)
    };
    ($scale:expr) => {
        (1.0, $scale, std::time::Duration::from_millis(200), $crate::easing::EASE_OUT_CUBIC)
    };
}

#[macro_export]
macro_rules! highlight {
    () => {
        (0.0, 1.0, std::time::Duration::from_millis(600), $crate::easing::EASE_OUT_CUBIC)
    };
    ($duration_ms:expr) => {
        (0.0, 1.0, std::time::Duration::from_millis($duration_ms), $crate::easing::EASE_OUT_CUBIC)
    };
}

#[macro_export]
macro_rules! glow {
    () => {
        (0.0, 1.0, std::time::Duration::from_millis(700), $crate::easing::EASE_OUT_CUBIC)
    };
    ($duration_ms:expr) => {
        (0.0, 1.0, std::time::Duration::from_millis($duration_ms), $crate::easing::EASE_OUT_CUBIC)
    };
}

#[macro_export]
macro_rules! pulse {
    () => {
        (0.0, 1.0, std::time::Duration::from_millis(1200), $crate::easing::EASE_IN_OUT_SINE)
    };
    ($duration_ms:expr) => {
        (0.0, 1.0, std::time::Duration::from_millis($duration_ms), $crate::easing::EASE_IN_OUT_SINE)
    };
}

// ==================== СКОРОСТНЫЕ ПРЕСЕТЫ ====================

#[macro_export]
macro_rules! instant {
    ($from:expr => $to:expr) => {
        ($from, $to, std::time::Duration::from_millis(200), $crate::easing::EASE_OUT_CUBIC)
    };
}

#[macro_export]
macro_rules! quick {
    ($from:expr => $to:expr) => {
        ($from, $to, std::time::Duration::from_millis(400), $crate::easing::EASE_OUT_CUBIC)
    };
    ($from:expr => $to:expr, $duration_ms:expr) => {
        ($from, $to, std::time::Duration::from_millis($duration_ms), $crate::easing::EASE_OUT_CUBIC)
    };
}

#[macro_export]
macro_rules! normal {
    ($from:expr => $to:expr) => {
        ($from, $to, std::time::Duration::from_millis(600), $crate::easing::EASE_OUT_CUBIC)
    };
}

#[macro_export]
macro_rules! smooth {
    ($from:expr => $to:expr) => {
        ($from, $to, std::time::Duration::from_millis(1000), $crate::easing::EASE_IN_OUT_CUBIC)
    };
}

#[macro_export]
macro_rules! deliberate {
    ($from:expr => $to:expr) => {
        ($from, $to, std::time::Duration::from_millis(1500), $crate::easing::EASE_IN_OUT_CUBIC)
    };
}

// ==================== UI-СПЕЦИФИЧНЫЕ ПРЕСЕТЫ ====================

#[macro_export]
macro_rules! modal {
    () => {
        (0.0, 1.0, std::time::Duration::from_millis(600), $crate::easing::EASE_OUT_BACK)
    };
    ($duration_ms:expr) => {
        (0.0, 1.0, std::time::Duration::from_millis($duration_ms), $crate::easing::EASE_OUT_BACK)
    };
}

#[macro_export]
macro_rules! tooltip {
    () => {
        (0.0, 1.0, std::time::Duration::from_millis(400), $crate::easing::EASE_OUT_CUBIC)
    };
    ($duration_ms:expr) => {
        (0.0, 1.0, std::time::Duration::from_millis($duration_ms), $crate::easing::EASE_OUT_CUBIC)
    };
}

#[macro_export]
macro_rules! dropdown {
    () => {
        (0.0, 1.0, std::time::Duration::from_millis(500), $crate::easing::EASE_OUT_BACK)
    };
    ($duration_ms:expr) => {
        (0.0, 1.0, std::time::Duration::from_millis($duration_ms), $crate::easing::EASE_OUT_BACK)
    };
}

#[macro_export]
macro_rules! notification {
    () => {
        (0.0, 1.0, std::time::Duration::from_millis(700), $crate::easing::EASE_OUT_BACK)
    };
    ($duration_ms:expr) => {
        (0.0, 1.0, std::time::Duration::from_millis($duration_ms), $crate::easing::EASE_OUT_BACK)
    };
}

#[macro_export]
macro_rules! drawer {
    () => {
        (0.0, 1.0, std::time::Duration::from_millis(700), $crate::easing::EASE_OUT_CUBIC)
    };
    ($duration_ms:expr) => {
        (0.0, 1.0, std::time::Duration::from_millis($duration_ms), $crate::easing::EASE_OUT_CUBIC)
    };
}

// ==================== КОМБИНИРОВАННЫЕ ПРЕСЕТЫ ====================

#[macro_export]
macro_rules! slide_and_fade {
    ($distance:expr) => {
        (-$distance, 0.0, std::time::Duration::from_millis(800), $crate::easing::EASE_OUT_BACK)
    };
    ($distance:expr, $duration_ms:expr) => {
        (-$distance, 0.0, std::time::Duration::from_millis($duration_ms), $crate::easing::EASE_OUT_BACK)
    };
}

#[macro_export]
macro_rules! scale_and_fade {
    () => {
        (0.0, 1.0, std::time::Duration::from_millis(700), $crate::easing::EASE_OUT_BACK)
    };
    ($duration_ms:expr) => {
        (0.0, 1.0, std::time::Duration::from_millis($duration_ms), $crate::easing::EASE_OUT_BACK)
    };
}

// ==================== СОСТОЯНИЯ И СТАТУСЫ ====================

#[macro_export]
macro_rules! success {
    () => {
        (0.0, 1.0, std::time::Duration::from_millis(800), $crate::easing::EASE_OUT_BOUNCE)
    };
}

#[macro_export]
macro_rules! error {
    () => {
        (0.0, 1.0, std::time::Duration::from_millis(700), $crate::easing::EASE_OUT_ELASTIC)
    };
}

#[macro_export]
macro_rules! warning {
    () => {
        (0.0, 1.0, std::time::Duration::from_millis(900), $crate::easing::EASE_OUT_BACK)
    };
}

#[macro_export]
macro_rules! loading {
    () => {
        (0.0, 1.0, std::time::Duration::from_millis(1200), $crate::easing::EASE_IN_OUT_CUBIC)
    };
}

#[macro_export]
macro_rules! attention {
    () => {
        (0.0, 1.0, std::time::Duration::from_millis(1000), $crate::easing::EASE_OUT_BOUNCE)
    };
}