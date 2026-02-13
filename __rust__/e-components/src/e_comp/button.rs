// use egui::{Color32, Context, Frame, Layout, Response, Ui};

// pub struct ButtonBuilder {
//     background: Color32,
//     text: String,
// }
// impl Default for ButtonBuilder {
//     fn default() -> Self {
//         Self {
//             background: Color32::WHITE,
//             text: String::default(),
//         }
//     }
// }

// impl ButtonBuilder {
//     pub fn new() -> Self {
//         Self {
//             ..Default::default()
//         }
//     }
//     pub fn background(mut self, color: Color32) -> Self {
//         self.background = color;
//         self
//     }

//     pub fn text(mut self, text: String) -> Self {
//         self.text = text;
//         self
//     }

//     /// Метод для отрисовки компонента с замыканием
//     pub fn show<F>(&mut self, ui: &mut Ui, content_builder: F) -> Response
//     where
//         F: FnOnce(&mut Ui) -> Response,
//     {
//         ui.add_sized(
//             [30.0, 20.0],
//             egui::Button::new(self.text.as_str()).fill(self.background),
//         )
//     }

//     /// Метод для отрисовки компонента без замыканием
//     pub fn show_basic(&mut self, ui: &mut Ui) -> Response {
//         self.show(ui, |ui| ui.response())
//     }
// }

// // pub fn show<F>(&mut self, ui: &mut Ui, content_builder: F) -> Response
// // where
// //     F: FnOnce(&mut Ui) -> Response,
// // {

use egui::{Color32, CornerRadius, Response, Stroke, Ui};

#[derive(Default, Clone)]
pub struct ButtonBuilder {
    text: String,
    background: Color32,
    text_color: Color32,
    stroke: Option<Stroke>,
    rounding: Option<CornerRadius>,
    hover_effect: Option<HoverEffect>,
    click_effect: Option<ClickEffect>,
    size: Option<[f32; 2]>,
}

#[derive(Default, Clone)]
pub struct HoverEffect {
    background: Option<Color32>,
    text_color: Option<Color32>,
    scale: Option<f32>,
}

#[derive(Default, Clone)]
pub struct ClickEffect {
    background: Option<Color32>,
    text_color: Option<Color32>,
    offset: Option<[f32; 2]>,
}

impl ButtonBuilder {
    pub fn new() -> Self {
        Self {
            background: Color32::from_rgb(70, 130, 180), // Steel blue
            text_color: Color32::WHITE,
            ..Default::default()
        }
    }

    pub fn background(mut self, color: Color32) -> Self {
        self.background = color;
        self
    }

    pub fn text(mut self, text: impl Into<String>) -> Self {
        self.text = text.into();
        self
    }

    pub fn text_color(mut self, color: Color32) -> Self {
        self.text_color = color;
        self
    }

    pub fn stroke(mut self, stroke: Stroke) -> Self {
        self.stroke = Some(stroke);
        self
    }

    pub fn rounding(mut self, rounding: CornerRadius) -> Self {
        self.rounding = Some(rounding);
        self
    }

    pub fn size(mut self, width: f32, height: f32) -> Self {
        self.size = Some([width, height]);
        self
    }

    pub fn hover_effect(mut self, effect: HoverEffect) -> Self {
        self.hover_effect = Some(effect);
        self
    }

    pub fn click_effect(mut self, effect: ClickEffect) -> Self {
        self.click_effect = Some(effect);
        self
    }

    pub fn show(&self, ui: &mut Ui) -> Response {
        let size = self.size.unwrap_or([80.0, 30.0]);
        let button = egui::Button::new(&self.text)
            .fill(self.background)
            // .text_color(self.text_color)
            .min_size(size.into());

        let button = if let Some(stroke) = self.stroke {
            button.stroke(stroke)
        } else {
            button
        };

        let button = if let Some(rounding) = self.rounding {
            button.corner_radius(rounding)
        } else {
            button
        };

        let response = ui.add(button);

        // Apply hover effects
        if response.hovered() {
            if let Some(hover_effect) = &self.hover_effect {
                let mut visuals = ui.visuals().clone();

                if let Some(bg) = hover_effect.background {
                    visuals.widgets.hovered.bg_fill = bg;
                }

                if let Some(text_color) = hover_effect.text_color {
                    visuals.widgets.hovered.fg_stroke = Stroke {
                        width: 1.0,
                        color: text_color,
                    };
                }

                ui.ctx().set_visuals(visuals);
            }
        }

        // Apply click effects
        if response.clicked() || response.is_pointer_button_down_on() {
            if let Some(click_effect) = &self.click_effect {
                let mut visuals = ui.visuals().clone();

                if let Some(bg) = click_effect.background {
                    visuals.widgets.active.bg_fill = bg;
                }

                if let Some(text_color) = click_effect.text_color {
                    visuals.widgets.active.fg_stroke = Stroke {
                        width: 1.0,
                        color: text_color,
                    };
                }

                ui.ctx().set_visuals(visuals);
            }
        }

        response
    }
}

// Helper methods for creating effects
impl ButtonBuilder {
    pub fn with_shadow(mut self) -> Self {
        self.stroke = Some(Stroke::new(
            1.0,
            Color32::from_rgba_premultiplied(0, 0, 0, 60),
        ));
        self
    }

    pub fn with_rounded_corners(mut self, radius: u8) -> Self {
        self.rounding = Some(CornerRadius::same(radius));
        self
    }

    pub fn with_hover_highlight(mut self) -> Self {
        self.hover_effect = Some(HoverEffect {
            background: Some(self.background.gamma_multiply(0.8)),
            text_color: Some(self.text_color),
            scale: Some(1.02),
        });
        self
    }

    pub fn with_click_feedback(mut self) -> Self {
        self.click_effect = Some(ClickEffect {
            background: Some(self.background.gamma_multiply(0.9)),
            text_color: Some(self.text_color),
            offset: Some([0.5, 0.5]),
        });
        self
    }
}
