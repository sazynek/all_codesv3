use iced::{
    alignment, executor, 
    widget::{button, column, container, row, scrollable, text, text_input, Space},
    Alignment, Application, Command, Element, Length, Theme,
};
use std::process::{Command as CommandSync, Stdio};
use std::io::{BufRead, BufReader};
use std::sync::{Arc, Mutex};
use std::thread;

#[derive(Debug, Clone)]
enum Message {
    CommandInputChanged(String),
    ExecuteCommand,
    StopCommand,
    CommandOutput(Vec<String>),  // Изменено: принимаем ВЕСЬ вывод сразу
    CommandFinished(bool),
    ClearOutput,
    Tick,
}

struct CommandRunner {
    command_input: String,
    output_lines: Vec<String>,
    is_running: bool,
    shared_output: Arc<Mutex<Vec<String>>>,
}

impl Default for CommandRunner {
    fn default() -> Self {
        Self {
            command_input: String::from("ls -la"),
            output_lines: Vec::new(),
            is_running: false,
            shared_output: Arc::new(Mutex::new(Vec::new())),
        }
    }
}

impl Application for CommandRunner {
    type Message = Message;
    type Theme = Theme;
    type Executor = executor::Default;
    type Flags = ();

    fn new(_flags: ()) -> (Self, Command<Message>) {
        (Self::default(), Command::none())
    }

    fn title(&self) -> String {
        String::from("Command Runner - REAL-TIME")
    }

    fn update(&mut self, message: Message) -> Command<Message> {
        match message {
            Message::CommandInputChanged(input) => {
                self.command_input = input;
                Command::none()
            }
            
            Message::ExecuteCommand => {
                if self.is_running {
                    return Command::none();
                }
                
                self.is_running = true;
                self.output_lines.clear();
                
                let command = self.command_input.clone();
                let shared_output = Arc::clone(&self.shared_output);
                
                // Очищаем предыдущий вывод
                {
                    let mut output = shared_output.lock().unwrap();
                    output.clear();
                }
                
                println!("🚀 Executing command: {}", command);
                
                // Запускаем команду в отдельном потоке с реальным временем
                thread::spawn(move || {
                    if let Err(e) = run_command_realtime(command, shared_output) {
                        eprintln!("Command error: {}", e);
                    }
                });
                
                Command::none()
            }
            
            Message::StopCommand => {
                self.is_running = false;
                self.output_lines.push("⏹️ Command stopped by user".to_string());
                println!("⏹️ Command stopped by user");
                Command::none()
            }
            
            Message::CommandOutput(new_lines) => {
                println!("📝 Adding {} lines to output", new_lines.len());
                
                // Добавляем ВСЕ новые строки сразу
                self.output_lines.extend(new_lines);
                
                // Ограничиваем размер вывода для производительности
                if self.output_lines.len() > 1000 {
                    self.output_lines.drain(0..500);
                }
                
                Command::none()
            }
            
            Message::CommandFinished(success) => {
                self.is_running = false;
                
                let status = if success { 
                    "✅ Command completed successfully!" 
                } else { 
                    "❌ Command failed!" 
                };
                
                println!("{}", status);
                self.output_lines.push(status.to_string());
                
                Command::none()
            }
            
            Message::ClearOutput => {
                self.output_lines.clear();
                println!("🧹 Output cleared");
                Command::none()
            }
            
            Message::Tick => {
                // Забираем ВСЕ новые строки из разделяемого буфера
                let new_lines = {
                    let mut output = self.shared_output.lock().unwrap();
                    if !output.is_empty() {
                        let lines: Vec<String> = output.drain(..).collect();
                        println!("🔄 Sending {} lines to UI", lines.len());
                        lines
                    } else {
                        Vec::new()
                    }
                };
                
                // Если есть новые строки, отправляем их ВСЕ сразу
                if !new_lines.is_empty() {
                    return Command::perform(
                        async move { new_lines },
                        Message::CommandOutput
                    );
                }
                
                Command::none()
            }
        }
    }

    fn view(&'_ self) -> Element<'_, Message> {
        let command_input = text_input("Enter shell command...", &self.command_input)
            .on_input(Message::CommandInputChanged)
            .padding(12)
            .size(15);

        let execute_button = if self.is_running {
            button("⏹️ Stop").on_press(Message::StopCommand)
        } else {
            button("🚀 Execute").on_press(Message::ExecuteCommand)
        }
        .padding(12);

        let clear_button = button("🧹 Clear")
            .on_press(Message::ClearOutput)
            .padding(12);

        // Вывод как в консоли - ПРОСТО ТЕКСТ
        let output_content = if self.output_lines.is_empty() {
            container(
                text("Output will appear here...")
                    .style(iced::theme::Text::Color(iced::Color::BLACK)),   
            )
            .width(Length::Fill)            
            .center_x()
            .center_y()
            .height(Length::Fill)
        } else {
            // Создаем один большой текст со всеми строками
            let full_output = self.output_lines.join("\n");
            
            container(
                scrollable(
                    text(full_output)
                        .size(13)
                        .font(iced::Font::MONOSPACE)
                        .style(iced::theme::Text::Color(iced::Color::BLACK))
                )
                .height(Length::Fill)
            )
            .padding(15)
            .width(Length::Fill)
            .height(Length::Fill)
        };

        let controls = row![
            command_input.width(Length::Fill),
            execute_button,
            clear_button,
        ]
        .spacing(8)
        .align_items(Alignment::Center);

        let content = column![
            container(
                text("🎯 Command Runner - REAL-TIME")
                    .size(22)
                    .style(iced::theme::Text::Color(iced::Color::BLACK))
            )
            .width(Length::Fill)
            .center_x(),
            controls,
            text("Output:").size(14).style(iced::theme::Text::Color(iced::Color::BLACK)),
            output_content.height(Length::Fill),
        ]
        .spacing(12)
        .padding(20)
        .height(Length::Fill);

        container(content)
            .width(Length::Fill)
            .height(Length::Fill)
            .center_x()
            .into()
    }

    fn subscription(&self) -> iced::Subscription<Message> {
        if self.is_running {
            iced::time::every(std::time::Duration::from_millis(50)) // Быстрые обновления
                .map(|_| Message::Tick)
        } else {
            iced::Subscription::none()
        }
    }
}

// 🚀 РЕАЛЬНОЕ ВРЕМЯ - УПРОЩЕННАЯ ВЕРСИЯ
fn run_command_realtime(command: String, shared_output: Arc<Mutex<Vec<String>>>) -> Result<(), Box<dyn std::error::Error>> {
    let mut child = CommandSync::new("sh")
        .arg("-c")
        .arg(&command)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()?;

    let stdout = child.stdout.take().expect("Failed to take stdout");
    let stderr = child.stderr.take().expect("Failed to take stderr");

    // Клонируем Arc для каждого потока
    let shared_stdout = Arc::clone(&shared_output);
    let shared_stderr = Arc::clone(&shared_output);
    let shared_final = Arc::clone(&shared_output);

    // Сохраняем handles потоков
    let stdout_handle = thread::spawn(move || {
        let reader = BufReader::new(stdout);
        for line in reader.lines() {
            match line {
                Ok(line) => {
                    println!("📥 stdout: {}", line);
                    let mut output = shared_stdout.lock().unwrap();
                    output.push(line);
                }
                Err(e) => {
                    println!("❌ Error reading stdout: {}", e);
                    break;
                }
            }
        }
    });

    let stderr_handle = thread::spawn(move || {
        let reader = BufReader::new(stderr);
        for line in reader.lines() {
            match line {
                Ok(line) => {
                    println!("📥 stderr: {}", line);
                    let mut output = shared_stderr.lock().unwrap();
                    output.push(format!("[stderr] {}", line));
                }
                Err(e) => {
                    println!("❌ Error reading stderr: {}", e);
                    break;
                }
            }
        }
    });

    // Ждем завершения команды в основном потоке
    let status = child.wait()?;

    // Ждем завершения потоков чтения
    stdout_handle.join().expect("stdout thread panicked");
    stderr_handle.join().expect("stderr thread panicked");

    // Добавляем сообщение о завершении
    {
        let mut output = shared_final.lock().unwrap();
        if status.success() {
            output.push("✅ Command completed successfully!".to_string());
        } else {
            output.push("❌ Command failed!".to_string());
        }
    }

    Ok(())
}

pub fn main() -> iced::Result {
    println!("🚀 Starting Command Runner application...");
    CommandRunner::run(iced::Settings {
        window: iced::window::Settings {
            size: iced::Size::new(800.0, 600.0),
            min_size: Some(iced::Size::new(600.0, 400.0)),
            ..Default::default()
        },
        default_font: iced::Font::MONOSPACE,
        ..Default::default()
    })
}