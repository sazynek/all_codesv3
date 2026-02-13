use iced::{
    Alignment, Background, Border, Color, Length, Padding, Theme,
    border::Radius,
    widget::{Column, button, column, container, container::Style, row, text},
};
use iced_anim::{Event, animation::animation};

use crate::{Editor, Msg};

pub fn sidebar(editor: &'_ Editor) -> iced::widget::Column<'_, Msg> {
    let buttons: iced::widget::Row<Msg> = row![
        button(text(&editor.sidebar.text))
            .on_press(Msg::StartAnimation(Event::Target(
                if editor.sidebar.is_active {
                    editor.sidebar.position.target() - 300.0
                } else {
                    editor.sidebar.position.target() + 300.0
                }
            )))
            .padding(Padding {
                right: 5.0,
                left: 5.0,
                top: 9.0,
                bottom: 9.0,
            })
    ]
    .spacing(0)
    .align_y(Alignment::Center)
    .height(Length::Fill);

    let mut texts: Column<Msg> = column![];

    for i in editor.elements.clone() {
        texts = texts.push(text(i).wrapping(text::Wrapping::None).color(Color {
            r: 0.5,
            g: 0.5,
            b: 0.5,
            a: 1.0,
        }));
    }
    // texts
    // texts.align_x(Alignment::Center).spacing(5)

    let animated_box = animation(
        &editor.sidebar.position,
        container(texts.spacing(5))
            .padding(Padding {
                left: *editor.sidebar.position.value(),
                top: 0.0,
                right: 0.0,
                bottom: 0.0,
            })
            .height(Length::Fill)
            .width(Length::Shrink)
            .align_x(Alignment::End)
            .style(|_: &Theme| Style {
                background: Some(Background::Color(Color::WHITE)),
                border: Border {
                    color: Color::BLACK,
                    width: 0.0,
                    radius: Radius {
                        top_left: 10.0,
                        top_right: 0.0,
                        bottom_right: 0.0,
                        bottom_left: 10.0,
                    },
                },
                ..Default::default()
            }),
    )
    .on_update(|s| Msg::StartAnimation(s));

    column![row![buttons, animated_box]]
        .spacing(0)
        .padding(0)
        .align_x(Alignment::End)
        .width(Length::Fill)
        .into()
}
