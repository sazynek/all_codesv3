use crate::components::{CommandsBlock, OutputPanel};
use crate::{App, Message};
use iced::widget::{container, row};
use iced::{Element, Length};

pub fn view(app: &'_ App) -> Element<'_, Message> {
    let filtered_commands = app.filtered_commands();
    let commands_block = CommandsBlock::view(filtered_commands, app.main_hovered_index);
    let output_panel = OutputPanel::view(&app.output_state);

    row![
        container(commands_block)
            .width(Length::Fill)
            .height(Length::Fill),
        output_panel
    ]
    .spacing(20)
    .height(Length::Fill)
    .into()
}
