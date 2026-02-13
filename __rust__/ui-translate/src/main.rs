use std::env;
use std::path::Path;

// use std::fs::OpenOptions;
// use std::io::Read;

// use iced::Command;
use iced::advanced::graphics::core::{font, window};
// use iced::futures::io;
use iced::widget::{column, container, progress_bar, row, text};
use iced::{Alignment, Element, Font, Length, Padding, Size};
// use iced_anim::{Animated, Easing};
use rfd::FileDialog;
use tokio::runtime::Runtime;
mod c_btn;
use c_btn::btn;

mod program;

struct Btn {
    state: bool,
    path: String,
    fullpath: String,
}
// struct Sidebar {
//     position: Animated<f32>,
//     is_active: bool,
//     text: String,
// }
struct Progress {
    value: f32,
    max: f32,
}
struct Editor {
    file1: Btn,
    file2: Btn,
    // sidebar: Sidebar,
    open_file_btn: Btn,
    progress: Progress,
    translated_world: String,
    dir: String,
}

impl Default for Editor {
    fn default() -> Self {
        Self {
            file1: Btn {
                state: false,
                path: String::from("Select File"),
                fullpath: String::default(),
            },
            file2: Btn {
                state: false,
                path: String::from("Select File"),
                fullpath: String::default(),
            },
            // sidebar: Sidebar {
            //     position: Animated::transition(-200.0, Easing::EASE),
            //     is_active: false,
            //     text: String::from("<"),
            // },
            open_file_btn: Btn {
                state: false,
                path: String::from("Open File"),
                fullpath: String::default(),
            },
            progress: Progress {
                value: 0.0,
                max: 100.0,
            },
            translated_world: String::from("Words translated: 0"),
            dir: env::current_dir().unwrap().to_string_lossy().to_string(),
        }
    }
}

#[derive(Debug, Clone)]
enum Msg {
    FileOpen(i32),
    Translate,
    OpenFile,
    // StartAnimation(Event<f32>),
}
fn update(editor: &mut Editor, msg: Msg) {
    // files
    match msg {
        Msg::FileOpen(number_btn) => {
            // println!("file");
            let (fullpath, file) = start_file_dialog(editor);

            match number_btn {
                1 => {
                    editor.file1.fullpath = fullpath;
                    editor.file1.path = file;
                    editor.file1.state = if editor.file1.path == "file not found" {
                        false
                    } else {
                        true
                    };
                }
                2 => {
                    editor.file2.path = file;
                    editor.file2.fullpath = fullpath;
                    editor.file2.state = if editor.file2.path == "file not found" {
                        false
                    } else {
                        true
                    };
                }
                _ => (),
            };
        }
        Msg::Translate => {
            let arr = Runtime::new()
                .unwrap()
                .block_on(program::program(
                    editor.file1.fullpath.clone(),
                    editor.file2.fullpath.clone(),
                    &mut editor.progress.value,
                    &mut editor.progress.max,
                ))
                .unwrap_or_else(|e| vec!["Error".to_string(), e.to_string()]);
            if arr.len() == 2 {
                if arr.first().unwrap() == "Error" {
                    editor.translated_world = format!("error: {}", arr.last().unwrap());
                }
            } else {
                editor.translated_world = format!("words translated: {}", arr.len() as u32);
            }
            // println!("elements = {:?} value={:?}", editor.elements, value);
        }
        Msg::OpenFile => {
            #[cfg(target_os = "windows")]
            let path = "files/result.docx";
            #[cfg(target_os = "linux")]
            let path = "files/result.odt";

            if Path::new(path).exists() {
                if let Err(e) = open::that(path) {
                    editor.open_file_btn.path =
                        format!(r"Error\n{}", e.to_string()[0..10].to_string());
                    editor.open_file_btn.state = false;
                }
                editor.open_file_btn.path = format!("Open File");
                editor.open_file_btn.state = true;
            } else {
                editor.open_file_btn.path = format!("Not exist path: {}", path);
                editor.open_file_btn.state = false;
            }
        } // Msg::StartAnimation(event) => {
          //     println!(
          //         "before pos {}, act = {}",
          //         editor.sidebar.position.value().floor(),
          //         editor.sidebar.is_active
          //     );
          //     editor.sidebar.is_active = if editor.sidebar.position.value().floor() >= 0.0 {
          //         true
          //     } else {
          //         false
          //     };
          //     editor.sidebar.text = if editor.sidebar.is_active {
          //         ">".to_string()
          //     } else {
          //         "<".to_string()
          //     };
          //     editor.sidebar.position.update(event);
          //     println!(
          //         "after pos {}, act = {}",
          //         editor.sidebar.position.value().floor(),
          //         editor.sidebar.is_active
          //     );
          // }
    }
}

fn view(editor: &'_ Editor) -> Element<'_, Msg> {
    column![
        container(
            column![
                text(String::from("Translator").to_uppercase())
                    .center()
                    .font(Font {
                        style: font::Style::Italic,
                        ..Default::default()
                    })
                    .size(30),
                text(&editor.translated_world)
                    .width(Length::Fill)
                    .align_x(Alignment::Start)
                    .align_y(Alignment::Start)
                    .font(Font {
                        style: font::Style::Italic,
                        weight: font::Weight::Bold,
                        ..Default::default()
                    })
                    .size(10),
                row![
                    btn(
                        text(editor.file1.path.to_string()).size(17).center(),
                        Some(editor.file1.state)
                    )
                    .padding(5)
                    .on_press(Msg::FileOpen(1)),
                    btn(
                        text(editor.file2.path.to_string()).size(17).center(),
                        Some(editor.file2.state)
                    )
                    .padding(5)
                    .on_press(Msg::FileOpen(2)),
                ]
                .align_y(Alignment::Center)
                .spacing(10),
                btn(
                    text("translate").size(17).center().width(Length::Fill),
                    None
                )
                .padding(Padding::from([10, 5]))
                .on_press(Msg::Translate),
                btn(
                    text(editor.open_file_btn.path.as_str())
                        .size(17)
                        .center()
                        .width(Length::Fill),
                    Some(editor.open_file_btn.state)
                )
                .padding(Padding::from([10, 5]))
                .on_press(Msg::OpenFile),
                progress_bar(0.0..=editor.progress.max, editor.progress.value),
            ]
            .spacing(15)
            .align_x(Alignment::Center)
        )
        .width(Length::Fill) // Ширина по контенту
        .height(Length::Fill) // Высота по контенту
        .padding(15)
        .center(Length::Fill)
        .align_x(Alignment::Center)
        .align_y(Alignment::Center)
    ]
    .into()
}

fn start_file_dialog(editor: &mut Editor) -> (String, String) {
    if let Some(file_path) = FileDialog::new()
        .add_filter("Text Files", &["txt"])
        .set_directory(&editor.dir) // Optional: set initial directory
        .pick_file()
    {
        let fullpath = file_path.to_string_lossy().to_string();
        let path = fullpath.split("/").last().unwrap().to_string();
        let array = fullpath
            .split("/")
            .into_iter()
            .map(|f| f)
            .collect::<Vec<&str>>();
        editor.dir = array[..array.len() - 1].join("/");
        println!("Current dir is {}", editor.dir);

        return (fullpath, path);
    }

    return (
        String::from("file not found"),
        String::from("file not found"),
    );
}
// fn read_file(string: &str, fs: &mut OpenOptions) -> Result<String, io::Error> {
//     let mut file_str = String::new();
//     let mut pb = fs.open(string)?;
//     pb.read_to_string(&mut file_str)?;

//     Ok(file_str)
// }

fn main() -> iced::Result {
    let settings = iced::window::Settings {
        size: Size::new(300.0, 300.0),
        max_size: Some(Size::new(600.0, 600.0)),
        min_size: Some(Size::new(300.0, 300.0)),
        resizable: true,
        position: window::Position::Centered,
        ..Default::default()
    };

    iced::application("Translator App", update, view)
        .window(settings)
        .run()
}
