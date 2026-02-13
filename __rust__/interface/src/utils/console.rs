use iced::Task;
use nix::unistd::Uid;
use std::process::Command;
use std::process::Stdio;
use std::sync::{Arc, Mutex};
use tokio::io::{AsyncBufReadExt, BufReader};
use tokio::process::Command as TokioCommand;
use tokio::sync::mpsc;

#[derive(Debug, Clone)]
pub struct CommandResult {
    pub success: bool,
    pub exit_code: Option<i32>,
}

#[derive(Debug, Clone)]
pub struct RunningCommand {
    pub command_index: usize,
    pub title: String,
    pub command: String,
}

pub struct ConsoleManager {
    pub output_buffer: Arc<Mutex<String>>,
    pub output_receiver: Option<mpsc::UnboundedReceiver<String>>,
    pub running_command: Option<RunningCommand>,
}

impl Default for ConsoleManager {
    fn default() -> Self {
        Self {
            output_buffer: Arc::new(Mutex::new(String::new())),
            output_receiver: None,
            running_command: None,
        }
    }
}

impl ConsoleManager {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn is_command_running(&self) -> bool {
        self.running_command.is_some()
    }

    pub fn start_command(
        &mut self,
        command_index: usize,
        command: String,
        title: String,
        need_root: bool,
    ) -> Result<(String, Task<CommandResult>), String> {
        // Обрабатываем команду с учетом need_root
        let processed_command = if need_root {
            self.process_sudo_command(&command)?
        } else {
            command.clone()
        };

        self.running_command = Some(RunningCommand {
            command_index,
            title: title.clone(),
            command: command.clone(),
        });

        // Очищаем буферы
        *self.output_buffer.lock().unwrap() = String::new();

        // Создаем канал для передачи вывода
        let (tx, rx) = mpsc::unbounded_channel();
        self.output_receiver = Some(rx);

        let initial_message = format!("🔄 Executing '{}'...\n", title);
        let task = self.execute_command_async(processed_command, tx);

        Ok((initial_message, task))
    }

    fn process_sudo_command(&self, command: &str) -> Result<String, String> {
        // Проверяем, является ли пользователь уже root
        if Uid::effective().is_root() {
            return Ok(command.to_string());
        }

        // Список графических утилит для sudo запросов (в порядке предпочтения)
        let sudo_wrappers = vec!["pkexec", "kdesudo", "gksudo", "gksu"];

        // Проверяем, содержит ли команда уже одну из утилит
        let has_wrapper = sudo_wrappers
            .iter()
            .any(|&wrapper| command.contains(wrapper));

        if has_wrapper {
            return Ok(command.to_string());
        }

        // Ищем доступную утилиту в системе
        for wrapper in sudo_wrappers {
            if self.is_wrapper_available(wrapper) {
                return Ok(format!("{} {}", wrapper, command));
            }
        }

        // Если не нашли доступную утилиту
        Err(
            "Для выполнения этой команды требуются права root, но не найдена ни одна из доступных утилит для графического запроса прав.\n\n\
            Пожалуйста, установите одну из следующих утилит:\n\
            - pkexec (часто уже установлен)\n\
            - kdesudo (для KDE)\n\
            - gksudo/gksu (для GNOME)\n\n\
            Или выполните команду вручную через терминал с sudo.".to_string()
        )
    }

    fn is_wrapper_available(&self, wrapper: &str) -> bool {
        if cfg!(target_os = "windows") {
            // В Windows проверяем через where
            Command::new("where")
                .arg(wrapper)
                .output()
                .map(|output| output.status.success())
                .unwrap_or(false)
        } else {
            // В Unix-системах проверяем через which или command -v
            Command::new("sh")
                .arg("-c")
                .arg(format!("command -v {}", wrapper))
                .output()
                .map(|output| output.status.success())
                .unwrap_or(false)
        }
    }

    pub fn check_for_new_output(&mut self, current_output: &mut String) -> bool {
        let mut has_new_output = false;

        if let Some(ref mut rx) = self.output_receiver {
            while let Ok(output_chunk) = rx.try_recv() {
                current_output.push_str(&output_chunk);
                has_new_output = true;
            }
        }

        has_new_output
    }

    pub fn finish_command(&mut self, result: CommandResult, current_output: &mut String) -> String {
        // Сначала проверяем оставшийся вывод
        self.check_for_new_output(current_output);

        // Затем извлекаем running_command чтобы освободить заимствование
        let running_cmd = self.running_command.take();

        if let Some(running_cmd) = running_cmd {
            let status_text = if result.success {
                format!(
                    "\n\n✅ Command '{}' completed successfully",
                    running_cmd.title
                )
            } else {
                format!(
                    "\n\n❌ Command '{}' failed with exit code: {:?}",
                    running_cmd.title, result.exit_code
                )
            };

            current_output.push_str(&status_text);

            // Очищаем состояние
            self.output_receiver = None;

            status_text
        } else {
            String::new()
        }
    }

    pub fn clear_output(&mut self, current_output: &mut String) {
        current_output.clear();
        *self.output_buffer.lock().unwrap() = String::new();
    }

    fn execute_command_async(
        &self,
        command: String,
        tx: mpsc::UnboundedSender<String>,
    ) -> Task<CommandResult> {
        let output_buffer = Arc::clone(&self.output_buffer);

        Task::perform(
            async move {
                let (cmd, args) = if cfg!(target_os = "windows") {
                    ("cmd", vec!["/C", &command])
                } else {
                    ("sh", vec!["-c", &command])
                };

                match TokioCommand::new(cmd)
                    .args(args)
                    .stdout(Stdio::piped())
                    .stderr(Stdio::piped())
                    .spawn()
                {
                    Ok(mut child) => {
                        let stdout = child.stdout.take().unwrap();
                        let stderr = child.stderr.take().unwrap();

                        let mut stdout_reader = BufReader::new(stdout).lines();
                        let mut stderr_reader = BufReader::new(stderr).lines();

                        // Читаем stdout и stderr параллельно
                        loop {
                            tokio::select! {
                                line = stdout_reader.next_line() => {
                                    match line {
                                        Ok(Some(line)) => {
                                            let output_line = format!("{}\n", line);
                                            // Сохраняем в буфер
                                            {
                                                let mut buffer = output_buffer.lock().unwrap();
                                                buffer.push_str(&output_line);
                                            }
                                            // Отправляем через канал
                                            let _ = tx.send(output_line);
                                        }
                                        Ok(None) => break,
                                        Err(_) => break,
                                    }
                                }
                                line = stderr_reader.next_line() => {
                                    match line {
                                        Ok(Some(line)) => {
                                            let output_line = format!("[stderr] {}\n", line);
                                            // Сохраняем в буфер
                                            {
                                                let mut buffer = output_buffer.lock().unwrap();
                                                buffer.push_str(&output_line);
                                            }
                                            // Отправляем через канал
                                            let _ = tx.send(output_line);
                                        }
                                        Ok(None) => break,
                                        Err(_) => break,
                                    }
                                }
                            }
                        }

                        let status = child.wait().await;
                        let success = status.as_ref().map(|s| s.success()).unwrap_or(false);
                        let exit_code = status.map(|s| s.code()).unwrap_or(None);

                        CommandResult { success, exit_code }
                    }
                    Err(e) => {
                        let error_msg = format!("Failed to spawn command: {}\n", e);
                        {
                            let mut buffer = output_buffer.lock().unwrap();
                            buffer.push_str(&error_msg);
                        }
                        let _ = tx.send(error_msg);

                        CommandResult {
                            success: false,
                            exit_code: None,
                        }
                    }
                }
            },
            |result| result,
        )
    }
}
