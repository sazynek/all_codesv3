use std::hash::{DefaultHasher, Hash, Hasher};

// sidebar.rs
use eframe::egui;
use egui::Id;

/// Переиспользуемый компонент сайдбара
pub struct Sidebar {
    visible: bool,
    width: f32,
    title: String,
}

impl Default for Sidebar {
    fn default() -> Self {
        Self {
            visible: false,
            width: 250.0,
            title: "Sidebar".to_string(),
        }
    }
}

impl Sidebar {
    /// Создает новый сайдбар с кастомными параметрами
    pub fn new(title: impl Into<String>, width: f32) -> Self {
        Self {
            visible: false,
            width,
            title: title.into(),
        }
    }

    /// Показывает или скрывает сайдбар
    pub fn toggle(&mut self) {
        self.visible = !self.visible;
    }

    /// Устанавливает видимость сайдбара
    pub fn set_visible(&mut self, visible: bool) {
        self.visible = visible;
    }

    /// Отображает сайдбар, если он видим
    pub fn show(&mut self, ctx: &egui::Context, content: impl FnOnce(&mut egui::Ui)) -> bool {
        let mut close_requested = false;

        if !self.visible {
            return close_requested;
        }

        let screen_rect = ctx.input(|i| i.screen_rect);
        let height = screen_rect.height();
        // let w = screen_rect;

        // let mut h = DefaultHasher::new();
        // 1.hash(&mut h);
        egui::Area::new(Id::from("area"))
            .fixed_pos(egui::pos2(screen_rect.right() - self.width, 0.0))
            .default_size(egui::vec2(self.width, height))
            .interactable(true)
            .show(ctx, |ui| {
                // Используем Frame с белым фоном
                egui::Frame::new()
                    .fill(egui::Color32::WHITE)
                    .inner_margin(egui::Margin::symmetric(16, 12)) // Отступы внутри frame
                    .corner_radius(egui::CornerRadius {
                        nw: 12, // Скругление top-left
                        ne: 0,  // Без скругления top-right
                        sw: 12, // Скругление bottom-left
                        se: 0,  // Без скругления bottom-right
                    })
                    .show(ui, |ui| {
                        // Устанавливаем черный цвет текста
                        ui.visuals_mut().override_text_color = Some(egui::Color32::BLACK);

                        ui.horizontal(|ui| {
                            ui.heading(&self.title);
                            ui.with_layout(
                                egui::Layout::right_to_left(egui::Align::Center),
                                |ui| {
                                    if ui.button("✖").clicked() {
                                        close_requested = true;
                                    }
                                },
                            );
                        });

                        ui.separator();
                        content(ui);
                    });
            });
        if close_requested {
            self.set_visible(false);
        }

        return close_requested;
    }
}
