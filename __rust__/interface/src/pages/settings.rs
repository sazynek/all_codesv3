use crate::components::SystemFilters;
use crate::{App, Message};
use iced::widget::{column, container, text};
use iced::{Element, Length};

pub fn view(app: &App) -> Element<'_, Message> {
    let system_filters = SystemFilters::view(
        app.show_linux,
        app.show_windows,
        app.show_macos,
        app.show_another,
        app.show_all,
    );

    container(
        column![
            text("Settings")
                .color(iced::Color::from_rgb(0.9, 0.9, 0.9))
                .size(24),
            system_filters
        ]
        .spacing(20)
        .align_x(iced::Alignment::Center),
    )
    .width(Length::Fill)
    .height(Length::Fill)
    .center_x(Length::Fill)
    .center_y(Length::Fill)
    .into()
}
