use std::collections::HashMap;

use crate::config::{AppSettings, load_config, load_settings, save_config, save_settings};
use crate::layout::{Footer, Header};

use crate::pages::{about, home, redactor, settings};
use crate::utils::console::{CommandResult, ConsoleManager};
use crate::utils::{CommandInfo, Page, RedactorFields, RedactorMessage, RedactorMode, System};
use arboard::Clipboard;
use iced::widget::{column, container};
use iced::{Element, Length, Subscription, Task, Theme};

pub mod components;
pub mod config;
pub mod layout;
pub mod pages;

pub mod utils;

pub fn main() -> iced::Result {
    iced::application("Graphic Commands", App::update, App::view)
        .subscription(App::subscription)
        .theme(|_| Theme::TokyoNight)
        .run()
}

#[derive(Debug, Clone)]
pub enum Message {
    // hovered+pressed affects
    MouseEnter(usize, Section),
    MouseLeave(Section),
    Pressed(usize, Section),
    // settings toggles
    ToggleSystem(System),
    ToggleAll,

    // commands
    DeleteCommand(usize),
    // Redactor
    RedactorMessage(RedactorMessage),

    // output
    ClearOutput,
    OutputCopy,
    CheckForNewOutput,
    CommandFinished(CommandResult),
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Section {
    Header,
    Main,
    Footer,
}

pub struct App {
    pub header: Header,
    pub footer: Footer,
    pub commands: Vec<CommandInfo>,
    pub main_hovered_index: Option<usize>,
    pub hovered_command: Option<String>,

    pub show_linux: bool,
    pub show_windows: bool,
    pub show_macos: bool,
    pub show_another: bool,
    pub show_all: bool,

    pub current_page: Page,

    pub title_input: String,
    pub command_input: String,

    pub redactor_title: String,
    pub redactor_command: String,
    pub redactor_system: System,

    pub output_state: components::output::OutputState,
    pub clipboard: Option<Clipboard>,
    pub current_output: String,
    pub console: ConsoleManager,
    pub need_root: bool,
    // redactor
    pub redactor_mode: RedactorMode,
    // pub redactor_error: String,
    // pub redactor_error_commands: String,
    pub redactor_error_real:HashMap<String, RedactorFields>,
}

impl Default for App {
    fn default() -> Self {
        let config = load_config();
        let settings = load_settings();

        let mut output_state = components::output::OutputState::new();
        output_state.set_text("Command output will appear here...");

        Self {
            header: Header::default(),
            footer: Footer::default(),
            commands: config.commands,
            main_hovered_index: None,
            hovered_command: None,

            show_linux: settings.show_linux,
            show_windows: settings.show_windows,
            show_macos: settings.show_macos,
            show_another: settings.show_another,
            show_all: settings.show_all,

            current_page: Page::Home,

            title_input: String::new(),
            command_input: String::new(),

            redactor_title: String::new(),
            redactor_command: String::new(),
            redactor_system: System::Any,

            output_state,
            clipboard: None,
            current_output: String::new(),
            console: ConsoleManager::new(),
            need_root: false,
            redactor_mode: RedactorMode::Create,
            // errors
            redactor_error: String::default(),
            redactor_error_commands: String::default(),
            redactor_error_real:HashMap::default(),
        }
    }
}

impl App {
    pub fn subscription(&self) -> Subscription<Message> {
        if self.console.is_command_running() {
            iced::time::every(std::time::Duration::from_millis(50))
                .map(|_| Message::CheckForNewOutput)
        } else {
            Subscription::none()
        }
    }
}

impl App {
    pub fn update(&mut self, message: Message) -> Task<Message> {
        match message {
            Message::CheckForNewOutput => {
                if self.console.check_for_new_output(&mut self.current_output) {
                    self.output_state.set_text(&self.current_output);
                }
                Task::none()
            }
            Message::MouseEnter(index, section) => {
                match section {
                    Section::Header => self.header.hovered_index = Some(index),
                    Section::Main => {
                        self.main_hovered_index = Some(index);
                        self.hovered_command = Some(self.commands[index].command.clone());
                    }
                    Section::Footer => self.footer.hovered_index = Some(index),
                }
                Task::none()
            }
            Message::MouseLeave(section) => {
                match section {
                    Section::Header => self.header.hovered_index = None,
                    Section::Main => {
                        self.main_hovered_index = None;
                        self.hovered_command = None;
                    }
                    Section::Footer => self.footer.hovered_index = None,
                }
                Task::none()
            }
            Message::Pressed(index, section) => {
                match section {
                    Section::Header => {
                        match index {
                            0 => self.current_page = Page::Home,
                            1 => self.current_page = Page::Redactor,
                            2 => self.current_page = Page::Settings,
                            3 => self.current_page = Page::About,
                            _ => {}
                        }
                        Task::none()
                    }
                    Section::Main => {
                        let cmd_info = &self.commands[index];

                        if !cmd_info.system.matches_current() {
                            self.current_output = format!(
                                "System mismatch: Command '{}' is for {:?}, but current system is different",
                                cmd_info.title, cmd_info.system
                            );
                            self.output_state.set_text(&self.current_output);
                            return Task::none();
                        }

                        if self.console.is_command_running() {
                            self.current_output =
                                "Another command is already running. Please wait.".to_string();
                            self.output_state.set_text(&self.current_output);
                            return Task::none();
                        }

                        // Запускаем команду через ConsoleManager с учетом need_root
                        match self.console.start_command(
                            index,
                            cmd_info.command.clone(),
                            cmd_info.title.clone(),
                            cmd_info.need_root,
                        ) {
                            Ok((initial_message, task)) => {
                                self.current_output = initial_message;
                                self.output_state.set_text(&self.current_output);
                                task.map(Message::CommandFinished)
                            }
                            Err(error_message) => {
                                self.current_output = error_message;
                                self.output_state.set_text(&self.current_output);
                                Task::none()
                            }
                        }
                    }
                    Section::Footer => Task::none(),
                }
            }
            Message::ClearOutput => {
                self.console.clear_output(&mut self.current_output);
                self.output_state.clear();
                Task::none()
            }
            Message::ToggleSystem(system) => {
                match system {
                    System::Linux => self.show_linux = !self.show_linux,
                    System::Windows => self.show_windows = !self.show_windows,
                    System::MacOS => self.show_macos = !self.show_macos,
                    System::Any => self.show_another = !self.show_another,
                }
                self.update_all_flag();
                self.save_settings();
                Task::none()
            }
            Message::ToggleAll => {
                if self.show_all {
                    self.show_linux = false;
                    self.show_windows = false;
                    self.show_macos = false;
                    self.show_another = false;
                    self.show_all = false;
                } else {
                    self.show_linux = true;
                    self.show_windows = true;
                    self.show_macos = true;
                    self.show_another = true;
                    self.show_all = true;
                }
                self.save_settings();
                Task::none()
            }

            Message::DeleteCommand(index) => {
                if index < self.commands.len() && !self.commands[index].default_command {
                    let command_title = self.commands[index].title.clone();
                    self.commands.remove(index);

                    let config = config::Config {
                        commands: self.commands.clone(),
                    };

                    if let Err(e) = save_config(&config) {
                        self.output_state
                            .set_text(&format!("Failed to delete command: {}", e));
                    } else {
                        self.output_state.set_text(&format!(
                            "Command '{}' deleted successfully!",
                            command_title
                        ));
                    }
                }
                Task::none()
            }
            Message::OutputCopy => {
                if self.clipboard.is_none() {
                    match Clipboard::new() {
                        Ok(clipboard) => {
                            self.clipboard = Some(clipboard);
                        }
                        Err(e) => {
                            eprintln!("Failed to access clipboard: {}", e);
                            return Task::none();
                        }
                    }
                }

                if let Some(ref mut clipboard) = self.clipboard {
                    let _ = clipboard.set_text(self.current_output.clone());
                }
                Task::none()
            }
            Message::CommandFinished(result) => {
                self.console
                    .finish_command(result, &mut self.current_output);
                self.output_state.set_text(&self.current_output);
                Task::none()
            }
            Message::RedactorMessage(redactor_message) => {
                redactor::redactor(self, redactor_message)
            }
        }
    }

    pub fn view(&'_ self) -> Element<'_, Message> {
        let main_content = match self.current_page {
            Page::Home => home::view(self),
            Page::Redactor => redactor::view(self),
            Page::Settings => settings::view(self),
            Page::About => about::view(self),
        };

        let content = column![
            container(self.header.view())
                .width(Length::Fill)
                .padding(10)
                .style(|_| container::Style {
                    background: Some(iced::Color::from_rgb(0.95, 0.95, 0.95).into()),
                    ..Default::default()
                }),
            container(main_content)
                .width(Length::Fill)
                .height(Length::Fill)
                .padding(20)
                .center_y(Length::Fill),
            container(self.footer.view(self.current_page)) // Передаем текущую страницу
                .width(Length::Fill)
                .padding(10)
                .style(|_| container::Style {
                    background: Some(iced::Color::from_rgb(0.95, 0.95, 0.95).into()),
                    ..Default::default()
                })
        ]
        .height(Length::Fill);

        container(content)
            .width(Length::Fill)
            .height(Length::Fill)
            .center_x(Length::Fill)
            .center_y(Length::Fill)
            .into()
    }

    fn update_all_flag(&mut self) {
        self.show_all =
            self.show_linux && self.show_windows && self.show_macos && self.show_another;
    }

    fn save_settings(&self) {
        let settings = AppSettings {
            show_linux: self.show_linux,
            show_windows: self.show_windows,
            show_macos: self.show_macos,
            show_another: self.show_another,
            show_all: self.show_all,
        };

        if let Err(e) = save_settings(&settings) {
            eprintln!("Failed to save settings: {}", e);
        }
    }

    pub fn filtered_commands(&self) -> Vec<(usize, &CommandInfo)> {
        self.commands
            .iter()
            .enumerate()
            .filter(|(_, cmd)| match cmd.system {
                System::Linux => self.show_linux,
                System::Windows => self.show_windows,
                System::MacOS => self.show_macos,
                System::Any => self.show_another,
            })
            .collect()
    }
}
