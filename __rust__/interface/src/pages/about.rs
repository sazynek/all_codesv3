use iced::widget::{container, text};
use iced::{Element, Length};

use crate::App;

pub fn view(_app: &App) -> Element<'static, crate::Message> {
    container(
        text("About")
            .color(iced::Color::from_rgb(0.9, 0.9, 0.9))
            .size(24),
    )
    .width(Length::Fill)
    .height(Length::Fill)
    .center_x(Length::Fill)
    .center_y(Length::Fill)
    .into()
}
