use egui::{Color32, Context, Frame, Layout, Response, Ui};
use egui_extras::Column;

pub struct HeaderBuilder {
    pub background: Color32,
    pub min_height: f32,
    pub max_height: f32,
}
impl Default for HeaderBuilder {
    fn default() -> Self {
        Self {
            background: Color32::WHITE,
            max_height: 200.0,
            min_height: 60.0,
        }
    }
}

impl HeaderBuilder {
    pub fn new() -> Self {
        Self {
            ..Default::default()
        }
    }
    pub fn background(mut self, color: Color32) -> Self {
        self.background = color;
        self
    }
    pub fn min_height(mut self, min_height: f32) -> Self {
        self.min_height = min_height;
        self
    }
    pub fn max_height(mut self, max_height: f32) -> Self {
        self.max_height = max_height;
        self
    }
    /// Метод для отрисовки компонента с замыканием
    pub fn show<F>(&mut self, ctx: &Context, content_builder: F) -> Response
    where
        F: FnOnce(&mut Ui) -> Response,
    {
        // let screen_rect = ctx.input(|i| i.screen_rect);
        // let width = screen_rect.width();
        let frame = self.frame();

        egui::TopBottomPanel::top("header")
            .frame(frame)
            .show_separator_line(false)
            .resizable(false)
            .show(ctx, |ui| {
                // ui.set_width(300.0);
                ui.set_height(20.0);
                ui.centered_and_justified(|ui| {
                    let a = ui.available_width() / 2.0;
                    println!(
                        "a: {a}, ui: {} 1920.0 - ui.width = {} current_pos: {}, separate: {}",
                        ui.available_width(),
                        1920.0 - ui.available_width(),
                        a - a / 2.0,
                        ui.available_width() / 3.0
                    );
                    ui.set_width(a - a / 2.0);
                    ui.horizontal_wrapped(|ui| {
                        content_builder(ui);
                    });
                });
            })
            .response
    }

    /// Метод для отрисовки компонента с замыканием
    pub fn show_basic(&mut self, ctx: &Context, ui: &mut Ui) -> Response {
        self.show(ctx, |ui| ui.response())
    }

    fn frame(&mut self) -> Frame {
        let frame = Frame::default()
            .fill(self.background) // Цвет фона
            .inner_margin(egui::Margin {
                top: 15,
                bottom: 15,
                right: 15,
                left: 15,
            }) // Внутренние отступы
            .outer_margin(egui::Margin {
                top: 0,
                bottom: 0,
                ..Default::default()
            })
            .corner_radius(egui::CornerRadius {
                se: 7,
                sw: 7,
                ..Default::default()
            }); // Скругление углов
        // .stroke(egui::Stroke::new(0.5, egui::Color32::GRAY));
        return frame;
    }
}

// pub fn show<F>(&mut self, ui: &mut Ui, content_builder: F) -> Response
// where
//     F: FnOnce(&mut Ui) -> Response,
// {
