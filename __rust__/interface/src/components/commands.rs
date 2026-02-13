use crate::{CommandInfo, Message, Section};
use iced::widget::{button, column, container, mouse_area, row, scrollable, text, tooltip};
use iced::{Border, Element, Length, border::Radius, mouse};

pub struct CommandsBlock;

impl CommandsBlock {
    pub fn view(
        filtered_commands: Vec<(usize, &CommandInfo)>,
        main_hovered_index: Option<usize>,
    ) -> Element<'static, Message> {
        let commands_scrollable = scrollable(filtered_commands.into_iter().fold(
            column!().spacing(8).width(Length::Fill),
            |col, (original_index, cmd_info)| {
                let is_hovered = Some(original_index) == main_hovered_index;
                let is_compatible = cmd_info.system.matches_current();

                let (text_color, bg_color) = if is_hovered {
                    if is_compatible {
                        (
                            iced::Color::from_rgb(0.0, 0.0, 0.0),
                            iced::Color::from_rgb(0.9, 0.9, 0.9),
                        )
                    } else {
                        (
                            iced::Color::from_rgb(0.0, 0.0, 0.0),
                            iced::Color::from_rgb(0.9, 0.7, 0.7),
                        )
                    }
                } else if is_compatible {
                    (
                        iced::Color::from_rgb(1.0, 1.0, 1.0),
                        iced::Color::from_rgb(0.3, 0.3, 0.3),
                    )
                } else {
                    (
                        iced::Color::from_rgb(1.0, 0.8, 0.8),
                        iced::Color::from_rgb(0.5, 0.2, 0.2),
                    )
                };

                let title_content = if cmd_info.default_command {
                    row![text(cmd_info.title.clone()).color(text_color).size(16),]
                } else {
                    row![
                        text("👤 ").size(12),
                        text(cmd_info.title.clone()).color(text_color).size(16),
                    ]
                };

                let command_button = mouse_area(
                    container(
                        row![
                            title_content,
                            text(format!(" [{:?}]", cmd_info.system))
                                .color(if is_compatible {
                                    iced::Color::from_rgb(0.0, 1.0, 0.0)
                                } else {
                                    iced::Color::from_rgb(1.0, 0.0, 0.0)
                                })
                                .size(12),
                        ]
                        .spacing(8)
                        .align_y(iced::Alignment::Center),
                    )
                    .padding(15)
                    .style(move |_| container::Style {
                        background: Some(bg_color.into()),
                        border: Border {
                            radius: Radius::from(8.0),
                            ..Default::default()
                        },
                        ..Default::default()
                    }),
                )
                .on_enter(Message::MouseEnter(original_index, Section::Main))
                .on_exit(Message::MouseLeave(Section::Main))
                .on_press(Message::Pressed(original_index, Section::Main))
                .interaction(mouse::Interaction::Pointer);

                let tooltip_text = format!("Execute: {}", cmd_info.command);

                let command_with_tooltip = tooltip(
                    command_button,
                    container(
                        text(tooltip_text)
                            .color(iced::Color::from_rgb(0.9, 0.9, 0.9))
                            .size(12),
                    )
                    .padding(8)
                    .style(|_| container::Style {
                        background: Some(iced::Color::from_rgb(0.3, 0.3, 0.5).into()),
                        border: Border {
                            radius: Radius::from(5.0),
                            ..Default::default()
                        },
                        ..Default::default()
                    }),
                    tooltip::Position::Bottom,
                );

                let command_row = if cmd_info.default_command {
                    row![command_with_tooltip,].width(Length::Fill)
                } else {
                    row![
                        command_with_tooltip,
                        button("❌")
                            .on_press(Message::DeleteCommand(original_index))
                            .padding(5)
                            .style(iced::widget::button::danger)
                    ]
                    .width(Length::Fill)
                    .spacing(5)
                    .align_y(iced::Alignment::Center)
                };

                col.push(command_row)
            },
        ))
        .height(300);

        container(
            column![
                text("Available Commands")
                    .color(iced::Color::from_rgb(0.9, 0.9, 0.9))
                    .size(18),
                commands_scrollable
            ]
            .spacing(10),
        )
        .padding(15)
        .width(Length::Fill)
        .height(400)
        .style(|_| container::Style {
            background: Some(iced::Color::from_rgb(0.2, 0.2, 0.25).into()),
            border: Border {
                radius: Radius::from(8.0),
                ..Default::default()
            },
            ..Default::default()
        })
        .into()
    }
}
