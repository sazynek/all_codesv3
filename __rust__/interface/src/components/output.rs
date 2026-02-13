use crate::Message;
use iced::widget::{Space, column, container, mouse_area, row, scrollable, text};
use iced::{Border, Element, Length, border::Radius, mouse};

pub struct OutputPanel;

#[derive(Debug, Default)]
pub struct OutputState {
    content: String,
}

impl OutputState {
    pub fn new() -> Self {
        Self {
            content: String::new(),
        }
    }

    pub fn set_text(&mut self, text: &str) {
        self.content = text.to_string();
    }

    pub fn clear(&mut self) {
        self.content.clear();
    }

    pub fn get_text(&self) -> &str {
        &self.content
    }

    pub fn append_text(&mut self, text: &str) {
        self.content.push_str(text);
    }
}

impl OutputPanel {
    pub fn view(state: &OutputState) -> Element<'_, Message> {
        container(
            column![
                row![
                    text("Command Output")
                        .color(iced::Color::from_rgb(0.9, 0.9, 0.9))
                        .size(18),
                    Space::with_width(Length::Fill),
                    row![
                        mouse_area(container(text("Copy")).padding(8).style(|_| {
                            container::Style {
                                background: Some(iced::Color::from_rgb(0.2, 0.5, 0.7).into()),
                                border: Border {
                                    radius: Radius::from(5.0),
                                    ..Default::default()
                                },
                                ..Default::default()
                            }
                        }))
                        .on_press(Message::OutputCopy)
                        .interaction(mouse::Interaction::Pointer),
                        mouse_area(container(text("Clear")).padding(8).style(|_| {
                            container::Style {
                                background: Some(iced::Color::from_rgb(0.6, 0.2, 0.2).into()),
                                border: Border {
                                    radius: Radius::from(5.0),
                                    ..Default::default()
                                },
                                ..Default::default()
                            }
                        }))
                        .on_press(Message::ClearOutput)
                        .interaction(mouse::Interaction::Pointer),
                    ]
                    .spacing(5)
                ]
                .align_y(iced::Alignment::Center),
                container(
                    scrollable(
                        container(
                            text(&state.content)
                                .color(iced::Color::from_rgb(0.9, 0.9, 0.9))
                                .size(12)
                                .font(iced::Font::MONOSPACE)
                        )
                        .padding(20) // Увеличенный отступ справа от скролла
                        .width(Length::Fill)
                    )
                    .width(Length::Fill)
                    .height(Length::Fill)
                )
                .width(Length::Fill)
                .height(300)
                .style(|_| container::Style {
                    background: Some(iced::Color::from_rgb(0.1, 0.1, 0.15).into()),
                    border: Border {
                        radius: Radius::from(5.0),
                        width: 1.0,
                        color: iced::Color::from_rgb(0.3, 0.3, 0.4),
                    },
                    ..Default::default()
                })
            ]
            .spacing(15),
        )
        .padding(15)
        .width(Length::Fill)
        .height(400)
        .style(|_| container::Style {
            background: Some(iced::Color::from_rgb(0.15, 0.15, 0.25).into()),
            border: Border {
                radius: Radius::from(8.0),
                width: 2.0,
                color: iced::Color::from_rgb(0.25, 0.25, 0.35),
            },
            ..Default::default()
        })
        .into()
    }
}
