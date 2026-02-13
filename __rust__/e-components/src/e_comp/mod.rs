mod button;
use button::ButtonBuilder;
use egui::{Color32, Ui};

#[derive(Clone)]
pub struct Ecomp {}

impl Default for Ecomp {
    fn default() -> Self {
        Self {}
    }
}
impl Ecomp {
    pub fn new() -> Self {
        Self {}
    }
}
impl Ecomp {
    // Функция-конструктор для удобного создания
    pub fn button(&self) -> ButtonBuilder {
        ButtonBuilder::new()
    }

    // Example usage
    pub fn show_fancy_button(&self, ui: &mut Ui) {
        let response = ButtonBuilder::new()
            .text("Click me!")
            .background(Color32::from_rgb(65, 105, 225)) // Royal blue
            .text_color(Color32::WHITE)
            .with_shadow()
            .with_rounded_corners(6)
            .with_hover_highlight()
            .with_click_feedback()
            .size(100.0, 40.0)
            .show(ui);

        if response.clicked() {
            println!("Button clicked!");
        }
    }
}
