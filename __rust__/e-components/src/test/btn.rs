use eframe::egui;
use egui::Id;
use std::time::Instant;

pub struct AnimatedButton {
    pub position: f32,    // Текущая позиция кнопки
    target_position: f32, // Целевая позиция
    animation_start: Option<Instant>,
    animation_duration: f32, // Длительность анимации в секундах
}

impl Default for AnimatedButton {
    fn default() -> Self {
        Self {
            position: 0.0,
            target_position: 0.0,
            animation_start: None,
            animation_duration: 0.3, // 300 мс
        }
    }
}

impl AnimatedButton {
    pub fn move_right(&mut self, amount: f32) {
        self.target_position += amount;
        self.animation_start = Some(Instant::now());
    }

    fn update_animation(&mut self, ctx: &egui::Context) {
        if let Some(start_time) = self.animation_start {
            let elapsed = start_time.elapsed().as_secs_f32();
            let progress = (elapsed / self.animation_duration).min(1.0);

            // Линейная интерполяция позиции
            self.position = lerp(self.position, self.target_position, progress);

            if progress < 1.0 {
                // Запрашиваем перерисовку для следующего кадра анимации
                ctx.request_repaint();
            } else {
                // Анимация завершена
                self.animation_start = None;
            }
        }
    }

    pub fn show(&mut self, ui: &mut egui::Ui) -> egui::Response {
        self.update_animation(ui.ctx());

        // Создаем область с анимированной позицией
        egui::Area::new(Id::from("hallopw"))
            .fixed_pos(egui::pos2(self.position, ui.cursor().top()))
            .show(ui.ctx(), |ui| ui.button("Нажми меня"))
            .inner
    }
}

// Функция линейной интерполяции
fn lerp(a: f32, b: f32, t: f32) -> f32 {
    a + (b - a) * t
}
