use crate::{App, Message, RedactorMessage, System};

use iced::border::{radius, rounded};
use iced::widget::{
    button, checkbox, column, container, horizontal_rule, pick_list, row, scrollable, text,
    text_input, vertical_space,
};
use iced::{Color, Element, Length, Theme};

pub fn create_mode_view(app: &App) -> Element<'_, Message> {
    // ЛЕВАЯ ПАНЕЛЬ - Карточка товара (превью команды)
    let command_preview = container(
        column![
            // Заголовок карточки
            container(text("Command Preview").size(18).color(Color::WHITE))
                .padding(8)
                .width(Length::Fill)
                .center_x(Length::Shrink),
            horizontal_rule(1),
            // Основная информация
            container(
                column![
                    // Иконка или заголовок
                    container(text("🚀").size(32))
                        .center_x(Length::Shrink)
                        .padding(10),
                    // Название команды
                    container(
                        text(if app.redactor_title.is_empty() {
                            "New Command"
                        } else {
                            &app.redactor_title
                        })
                        .size(20)
                        .width(Length::Fill)
                        .color(if app.redactor_title.is_empty() {
                            Color::from_rgba8(150, 150, 150, 1.0)
                        } else {
                            Color::WHITE
                        })
                    )
                    .center_x(Length::Shrink)
                    .padding([0, 10]),
                    // Система
                    container(
                        row![
                            text("System:").size(14),
                            text(format!("{:?}", app.redactor_system))
                                .size(14)
                                .color(Color::from_rgba8(100, 200, 255, 1.0))
                        ]
                        .spacing(5)
                    )
                    .padding([0, 5]),
                    // Требуются root права
                    if app.need_root {
                        container(
                            row![
                                text("🔐").size(14),
                                text("Requires root privileges")
                                    .size(12)
                                    .color(Color::from_rgba8(255, 100, 100, 1.0))
                            ]
                            .spacing(5),
                        )
                        .padding([0, 5])
                    } else {
                        // column![]
                        container(column![])
                    },
                    vertical_space(),
                    // Предпросмотр команды
                    container(
                        column![
                            text("Command Preview:").size(12),
                            container(
                                text(if app.redactor_command.is_empty() {
                                    "Your command will appear here..."
                                } else {
                                    &app.redactor_command
                                })
                                .size(12)
                                .color(
                                    if app.redactor_command.is_empty() {
                                        Color::from_rgba8(150, 150, 150, 1.0)
                                    } else {
                                        Color::from_rgba8(200, 200, 255, 1.0)
                                    }
                                )
                            )
                            .padding(10)
                            .style(|theme: &Theme| {
                                let palette = theme.extended_palette();
                                container::Style {
                                    background: Some(palette.background.weak.color.into()),
                                    border: iced::Border {
                                        radius: 8.0.into(),
                                        ..Default::default()
                                    },
                                    ..Default::default()
                                }
                            })
                            .width(Length::Fill)
                        ]
                        .spacing(5)
                    )
                    .width(Length::Fill)
                ]
                .spacing(10)
            )
            .padding(20)
            .width(Length::Fill)
        ]
        .spacing(10),
    )
    .width(Length::FillPortion(2)) // 2/5 ширины
    .style(|theme: &Theme| {
        let palette = theme.extended_palette();
        container::Style {
            background: Some(palette.background.base.color.into()),
            border: iced::Border {
                radius: 12.0.into(),
                width: 1.0,
                color: palette.background.strong.color,
            },
            ..Default::default()
        }
    });

    // ПРАВАЯ ПАНЕЛЬ - Настройки (со скроллом)
    let settings_panel = container(
        scrollable(
            column![
                // Заголовок настроек
                container(text("Command Settings").size(20).color(Color::WHITE))
                    .padding([15, 20])
                    .width(Length::Fill)
                    .center_x(Length::Fill),
                // Поле названия
                container(
                    column![
                        text("Command Title*")
                            .size(14)
                            .color(Color::from_rgba8(200, 200, 200, 1.0)),
                        text_input("Enter command title", &app.redactor_title)
                            .on_input(|s| Message::RedactorMessage(RedactorMessage::RedactorTitle(
                                s
                            )))
                            .padding(12),
                        // error
                        container(
                            text(app.redactor_error.to_string())
                                .size(11)
                                .color(Color::from_rgba8(255, 0, 0, 1.0))
                        )
                        .center(Length::Shrink)
                        .padding(2),
                    ]
                    .spacing(5)
                )
                .padding([0, 10]),
                // Поле команды
                container(
                    column![
                        text("Command*")
                            .size(14)
                            .color(Color::from_rgba8(200, 200, 200, 1.0)),
                        text_input("Enter your command", &app.redactor_command)
                            .on_input(|s| Message::RedactorMessage(
                                RedactorMessage::RedactorCommand(s)
                            ))
                            .padding(12),
                        // error
                        container(
                            text(app.redactor_error_commands.to_string())
                                .size(11)
                                .color(Color::from_rgba8(255, 0, 0, 1.0))
                        )
                        .center(Length::Shrink)
                        .padding(2),
                    ]
                    .spacing(5)
                )
                .padding([0, 10]),
                // Настройка системы
                container(
                    column![
                        text("Target System")
                            .size(14)
                            .color(Color::from_rgba8(200, 200, 200, 1.0)),
                        pick_list(System::all(), Some(app.redactor_system), |s| {
                            Message::RedactorMessage(RedactorMessage::RedactorSetSystem(s))
                        })
                        .padding(10)
                        .width(Length::Fill)
                    ]
                    .spacing(8)
                )
                .padding([0, 20]),
                // Checkbox root прав
                container(
                    checkbox("Require root privileges", app.need_root)
                        .on_toggle(|s| Message::RedactorMessage(
                            RedactorMessage::RedactorSetNeedRoot(s)
                        ))
                        .size(16)
                )
                .padding([0, 25]),
                // Кнопка добавления
                container(
                    button(
                        container(text("Add Command").size(16).color(Color::WHITE))
                            .padding(15)
                            .center_x(Length::Shrink)
                            .width(Length::Fill)
                    )
                    .on_press(Message::RedactorMessage(
                        RedactorMessage::RedactorAddCommand
                    ))
                    .style(|theme: &Theme, _| {
                        let palette = theme.extended_palette();
                        button::Style {
                            background: Some(palette.primary.strong.color.into()),
                            border: rounded(radius(8)),
                            text_color: palette.primary.strong.text,
                            ..Default::default()
                        }
                    })
                    .width(Length::Fill)
                )
                .padding([10, 5]),
                // Текстовое пояснение
                container(
                    text("* All fields are required")
                        .size(12)
                        .color(Color::from_rgba8(150, 150, 150, 1.0))
                )
                .padding([5, 20])
                .center_x(Length::Fill),
            ]
            .spacing(5)
            .padding(30), // Внутренний отступ для скролла
        )
        .height(Length::Fill)
        .width(Length::Fill),
    )
    .width(Length::FillPortion(3)) // 3/5 ширины
    .style(|theme: &Theme| {
        let palette = theme.extended_palette();
        container::Style {
            background: Some(palette.background.weak.color.into()),
            border: rounded(radius(2)),
            // : ,
            ..Default::default()
        }
    });

    // Основной layout
    let main_content = row![command_preview, settings_panel,]
        .spacing(20)
        .width(Length::Fill)
        .height(Length::Fill);

    column![
        // Заголовок страницы
        container(text("Create New Command").size(24).color(Color::WHITE))
            .padding([20, 15])
            .width(Length::Fill)
            .center_x(Length::Fill),
        // Основное содержимое
        container(main_content)
            .padding(20)
            .width(Length::Fill)
            .height(Length::Fill),
    ]
    .spacing(15)
    .width(Length::Fill)
    .height(Length::Fill)
    .into()
}




                        // error
                        // container(
                        //     text(app.redactor_error.to_string())
                        //         .size(11)
                        //         .color(Color::from_rgba8(255, 0, 0, 1.0))
                        // )
                        // .center(Length::Shrink)
                        // .padding(2),