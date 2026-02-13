use iced::{
    Background, Border, Color, Element, Length,
    widget::{Button, button},
};

use crate::Msg;

pub fn btn<'a, Content>(content: Content, state: Option<bool>) -> Button<'a, Msg>
where
    Content: Into<Element<'a, Msg>>,
{
    // Определяем базовые цвета в зависимости от состояния
    let (base_color, hover_color, text_color) = match state {
        Some(true) => (
            Color::from_rgb(0.36, 0.80, 0.36), // Красивый зеленый при наличии файла
            Color::from_rgb(0.28, 0.70, 0.28), // Темнее зеленый при наведении
            Color::WHITE,                      // Белый текст для контраста
        ),
        Some(false) => (
            Color::from_rgb(0.91, 0.30, 0.24), // Красивый красный при отсутствии файла
            Color::from_rgb(0.80, 0.20, 0.20), // Темнее красный при наведении
            Color::WHITE,                      // Белый текст для контраста
        ),
        None => (
            Color::from_rgb(0.47, 0.47, 0.47), // Нейтральный серый
            Color::from_rgb(0.40, 0.40, 0.40), // Темнее серый при наведении
            Color::WHITE,                      // Белый текст
        ),
    };

    button(content)
        .style(move |_: &iced::Theme, status: button::Status| {
            // Стиль с красивыми скругленными углами и тенями
            let border = Border {
                radius: iced::border::Radius::from(8.0),
                width: 1.0,
                color: match status {
                    button::Status::Hovered => Color::from_rgba(1.0, 1.0, 1.0, 0.2),
                    _ => Color::TRANSPARENT,
                },
            };

            match status {
                button::Status::Active => button::Style {
                    background: Some(Background::Color(base_color)),
                    text_color,
                    border,
                    shadow: Default::default(),
                },
                button::Status::Hovered => button::Style {
                    background: Some(Background::Color(hover_color)),
                    text_color,
                    border,
                    shadow: Default::default(),
                },
                button::Status::Pressed => button::Style {
                    background: Some(Background::Color(Color::from_rgb(
                        base_color.r * 0.9, // Затемняем на 10% при нажатии
                        base_color.g * 0.9,
                        base_color.b * 0.9,
                    ))),
                    text_color,
                    border,
                    shadow: Default::default(),
                },
                button::Status::Disabled => button::Style {
                    background: Some(Background::Color(Color::from_rgba(
                        base_color.r,
                        base_color.g,
                        base_color.b,
                        0.5,
                    ))),
                    text_color: Color::from_rgba(0.9, 0.9, 0.9, 0.7),
                    border,
                    shadow: Default::default(),
                },
            }
        })
        .width(Length::Fill)
        .padding(12) // Немного больше паддинг для лучшего внешнего вида
        .into()
}
