use crate::{App, Message};
use iced::widget::{column, container, text};
use iced::{Element, Length};

pub fn redact_mode_view(_app: &App) -> Element<'_, Message> {
    let content = container(
        column![
            text("Redact Mode").size(24),
            text("Edit existing commands and command combinations")
                .size(16)
                .color(iced::Color::from_rgb(0.8, 0.8, 0.8)),
            container(
                text("This feature is under development...")
                    .color(iced::Color::from_rgb(0.6, 0.6, 0.6))
                    .size(14)
            )
            .padding(20)
            .center_x(Length::Fill)
            .center_y(Length::Fill)
        ]
        .spacing(20)
        .align_x(iced::Alignment::Center),
    )
    .padding(40)
    .width(Length::Fill)
    .height(Length::Fill)
    .center_x(Length::Fill)
    .center_y(Length::Fill)
    .style(|_| container::Style {
        background: Some(iced::Color::from_rgb(0.1, 0.1, 0.1).into()),
        border: iced::Border {
            radius: iced::border::Radius::from(10.0),
            ..Default::default()
        },
        ..Default::default()
    });

    column![content].spacing(20).into()
}
