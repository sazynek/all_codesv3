use std::collections::HashMap;

use crate::config::save_config;
use crate::pages::redactor::combine::combine_mode_view;
use crate::pages::redactor::create::create_mode_view;
use crate::pages::redactor::redact::redact_mode_view;
use crate::utils::{CommandInfo, RedactorFields, RedactorMessage, System};
use crate::{App, Message, RedactorMode, config};
use iced::{Element, Task};
mod combine;
mod create;
mod redact;

pub fn view(app: &App) -> Element<'_, Message> {
    match app.redactor_mode {
        RedactorMode::Create => create_mode_view(app),
        RedactorMode::Combine => combine_mode_view(app),
        RedactorMode::Redact => redact_mode_view(app),
    }
}

pub fn redactor(app: &mut App, msg: RedactorMessage) -> Task<Message> {
    match msg {
        RedactorMessage::RedactorTitle(value) => {
            app.redactor_title = value;
            Task::none()
        }

        RedactorMessage::RedactorCommand(value) => {
            app.redactor_command = value;
            Task::none()
        }
        RedactorMessage::RedactorSetSystem(system) => {
            app.redactor_system = system;
            Task::none()
        }
        RedactorMessage::RedactorModeChanged(redactor_mode) => {
            app.redactor_mode = redactor_mode;
            Task::none()
        }
        RedactorMessage::RedactorSetNeedRoot(is_need_root) => {
            app.need_root = is_need_root;
            Task::none()
        }
        RedactorMessage::RedactorAddCommand => {
            // app.redactor_error_real

            // let m=map["f".to_string()];
            
            
            if app.redactor_title.is_empty() {
                
                app.redactor_error = "not fount title".to_string();
            } else {
                app.redactor_error = "".to_string();
            }
            if app.redactor_command.is_empty() {
                app.redactor_error_commands = "not fount commands".to_string();
            } else {
                app.redactor_error_commands = "".to_string();
            }
            if app.redactor_command.is_empty() || app.redactor_title.is_empty() {
                return Task::none();
            }

            let new_command = CommandInfo::new(
                &app.redactor_title,
                &app.redactor_command,
                app.redactor_system,
                false,
                app.need_root,
            );

            app.commands.push(new_command);
            // #[allow(unreachable_code)]
            let config = config::Config {
                commands: app.commands.clone(),
            };

            if let Err(e) = save_config(&config) {
                app.output_state
                    .set_text(&format!("Failed to save command: {}", e));
            } else {
                app.output_state.set_text(&format!(
                    "Command '{}' added successfully for {:?}!",
                    app.redactor_title, app.redactor_system
                ));
                app.redactor_title.clear();
                app.redactor_command.clear();
                app.redactor_system = System::Any;
            }

            Task::none()
        }
    }
}
