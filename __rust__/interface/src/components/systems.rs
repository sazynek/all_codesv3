use crate::{Message, System};
use iced::widget::{Space, checkbox, column, container, row, text};
use iced::{Border, Element, Length, border::Radius};

pub struct SystemFilters;

impl SystemFilters {
    pub fn view(
        show_linux: bool,
        show_windows: bool,
        show_macos: bool,
        show_another: bool,
        show_all: bool,
    ) -> Element<'static, Message> {
        container(
            column![
                text("System Filters")
                    .color(iced::Color::from_rgb(0.9, 0.9, 0.9))
                    .size(18),
                row![
                    checkbox("Linux", show_linux)
                        .on_toggle(|_| Message::ToggleSystem(System::Linux)),
                    checkbox("Windows", show_windows)
                        .on_toggle(|_| Message::ToggleSystem(System::Windows)),
                    checkbox("MacOS", show_macos)
                        .on_toggle(|_| Message::ToggleSystem(System::MacOS)),
                    checkbox("Other", show_another)
                        .on_toggle(|_| Message::ToggleSystem(System::Any)),
                    Space::with_width(Length::Fill),
                    checkbox("All", show_all).on_toggle(|_| Message::ToggleAll)
                ]
                .spacing(15)
                .align_y(iced::Alignment::Center)
            ]
            .spacing(10),
        )
        .padding(15)
        .style(|_| container::Style {
            background: Some(iced::Color::from_rgb(0.25, 0.25, 0.35).into()),
            border: Border {
                radius: Radius::from(8.0),
                ..Default::default()
            },
            ..Default::default()
        })
        .into()
    }
}
