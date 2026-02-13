use crate::{Message, Section};
use iced::widget::{container, mouse_area, row, text};
use iced::{Element, Length, mouse};

#[derive(Debug, Clone, Default)]
pub struct Header {
    pub hovered_index: Option<usize>,
}

impl Header {
    pub fn view(&'_ self) -> Element<'_, Message> {
        let menu_items = vec!["Home", "Redactor", "Settings", "About"];

        let menu_row =
            menu_items
                .into_iter()
                .enumerate()
                .fold(row!().spacing(20), |row, (index, item)| {
                    let is_hovered = self.hovered_index == Some(index);
                    let text_color = if is_hovered {
                        iced::Color::from_rgb(0.2, 0.2, 0.7)
                    } else {
                        iced::Color::from_rgb(0.3, 0.3, 0.3)
                    };

                    row.push(
                        mouse_area(container(text(item).color(text_color).size(16)).padding(10))
                            .on_enter(Message::MouseEnter(index, Section::Header))
                            .on_exit(Message::MouseLeave(Section::Header))
                            .on_press(Message::Pressed(index, Section::Header))
                            .interaction(if is_hovered {
                                mouse::Interaction::Pointer
                            } else {
                                mouse::Interaction::default()
                            }),
                    )
                });

        container(menu_row)
            .width(Length::Shrink)
            .center(Length::Shrink)
            .into()
    }
}
