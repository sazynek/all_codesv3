use crate::utils::RedactorMode;
use crate::{Message, Page, Section};
use iced::border::Radius;
use iced::mouse::Interaction;
use iced::widget::{Space, container, mouse_area, row, text};
use iced::{Border, Element, Length};

pub struct Footer {
    pub words: Vec<String>,
    pub hovered_index: Option<usize>,
}

impl Default for Footer {
    fn default() -> Self {
        Self {
            words: vec!["Privacy".into(), "Terms".into(), "Copyright".into()],
            hovered_index: None,
        }
    }
}

impl Footer {
    pub fn view(&'_ self, current_page: Page) -> Element<'_, Message> {
        let footer_content = match current_page {
            Page::Home => self.home_footer(),
            Page::Redactor => self.redactor_footer(),
            Page::Settings => self.settings_footer(),
            Page::About => self.about_footer(),
        };

        container(footer_content)
            .padding(4)
            .style(|_| container::Style {
                background: Some(iced::Color::from_rgb(0.95, 0.95, 0.95).into()),
                ..Default::default()
            })
            .width(Length::Fill)
            .into()
    }

    fn home_footer(&'_ self) -> Element<'_, Message> {
        container(
            row![
                Space::with_width(Length::Fill),
                text("Home - Command Management Interface")
                    .color(iced::Color::from_rgb(0.2, 0.2, 0.2))
                    .size(12),
                Space::with_width(Length::Fill)
            ]
            .align_y(iced::Alignment::Center)
            .width(Length::Fill),
        )
        .into()
    }

    fn redactor_footer(&'_ self) -> Element<'_, Message> {
        let mode_buttons = [
            ("create", RedactorMode::Create),
            ("combine", RedactorMode::Combine),
            ("redact", RedactorMode::Redact),
        ];

        let buttons_row: Vec<Element<Message>> = mode_buttons
            .iter()
            .enumerate()
            .map(|(index, (label, mode))| {
                mouse_area(
                    container(
                        text(*label)
                            .color(iced::Color::from_rgb(0.2, 0.2, 0.2))
                            .size(12),
                    )
                    .padding(6)
                    .style(move |_| {
                        if Some(index) == self.hovered_index {
                            container::Style {
                                background: Some(iced::Color::from_rgb(0.9, 0.9, 0.8).into()),
                                border: Border {
                                    radius: Radius::from(3.0),
                                    ..Default::default()
                                },
                                ..Default::default()
                            }
                        } else {
                            container::Style::default()
                        }
                    }),
                )
                .on_press(Message::RedactorMessage(
                    crate::utils::RedactorMessage::RedactorModeChanged(*mode),
                )) // Добавляем обработчик нажатия
                .on_enter(Message::MouseEnter(index, Section::Footer))
                .on_exit(Message::MouseLeave(Section::Footer))
                .interaction(Interaction::Pointer)
                .into()
            })
            .collect();

        container(
            row![
                Space::with_width(Length::Fill),
                row(buttons_row).spacing(8),
                Space::with_width(Length::Fill)
            ]
            .align_y(iced::Alignment::Center)
            .width(Length::Fill),
        )
        .into()
    }

    fn settings_footer(&'_ self) -> Element<'_, Message> {
        container(
            row![
                Space::with_width(Length::Fill),
                text("Settings - Application Configuration")
                    .color(iced::Color::from_rgb(0.2, 0.2, 0.2))
                    .size(12),
                Space::with_width(Length::Fill)
            ]
            .align_y(iced::Alignment::Center)
            .width(Length::Fill),
        )
        .into()
    }

    fn about_footer(&'_ self) -> Element<'_, Message> {
        container(
            row![
                Space::with_width(Length::Fill),
                text("About - Graphic Commands Application")
                    .color(iced::Color::from_rgb(0.2, 0.2, 0.2))
                    .size(12),
                Space::with_width(Length::Fill)
            ]
            .align_y(iced::Alignment::Center)
            .width(Length::Fill),
        )
        .into()
    }
}
