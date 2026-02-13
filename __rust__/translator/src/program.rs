use docx_rust::{
    Docx,
    document::{Paragraph, Run, Text},
};
use futures::future::join_all;
use regex::Regex;
use rust_translate::translate_from_english;
use std::{
    fs::{self, OpenOptions},
    io::{Read, stdin},
    path::Path,
    process::Command,
};
// constants
const PLACEHOLDER: &str = "Введите путь к файлу";
const FILENAME: &str = "files";

pub async fn program() {
    //variables
    let mut tasks: Vec<_> = Vec::new();
    let mut text1 = String::new();
    let mut text2 = String::new();
    let main_docx_file_name = String::from("result.docx");

    mkdir(FILENAME).expect("not Found file  name");
    // file number 1
    input(&mut text1, PLACEHOLDER);
    reader(&mut text1);
    let v1 = filter_word(text1);
    // file number 2
    input(&mut text2, PLACEHOLDER);
    reader(&mut text2);
    let v2 = filter_word(text2);

    println!("Начинаю поиск слов в тексте\n");
    let exist_words = equals(v1, v2);

    println!("Начинаю переводить\n");
    for i in exist_words {
        let future_item = translate_(i);
        tasks.push(future_item);
    }

    let finall = join_all(tasks).await; //get translated world from the tasks(translate function)
    println!("Всего слов с переводом: {}\n", finall.len());

    #[cfg(target_os = "windows")]
    println!("Создаю word (.docx/.doc) файл\n");
    #[cfg(target_os = "linux")]
    println!("Создаю libreoffice (.odt) файл\n");

    write_docx(finall, main_docx_file_name).expect("Error writing file");
}

fn input(buf: &mut String, str: &str) {
    println!("{str}:");
    stdin().read_line(buf).unwrap();
}

fn reader(path: &mut String) {
    if !Path::new(path.trim()).exists() {
        panic!("!!!\nFile not found -- {} --\n!!!", path.trim());
    }

    let mut reader_var = OpenOptions::new()
        .read(true)
        .open(path.trim())
        .expect("Not file open");
    path.clear();
    reader_var.read_to_string(path).unwrap();
}

fn filter_word<'a>(text: String) -> Vec<String> {
    // println!("Pattern");
    let pattern = r"[A-Za-z]{4,}";
    let re = Regex::new(pattern).expect("Regex error");
    let mut vec: Vec<String> = re
        .find_iter(&text)
        .map(|v| v.as_str().to_string())
        .collect();

    println!("Слов: {}", vec.len());
    vec.sort();
    vec.dedup();
    println!("Слов после фильтрации: {}", vec.len());

    return vec;
}

fn equals<'a>(mut values1: Vec<String>, mut values2: Vec<String>) -> Vec<String> {
    values1.sort();
    values2.sort();

    let mut vec: Vec<String> = Vec::new();
    for i in values1 {
        let inner_i = i.trim().to_string().to_lowercase();

        if inner_i == " " {
            continue;
        }

        for j in values2.iter() {
            let inner_j = j.trim().to_string().to_lowercase();
            let first_ch_j = inner_j.chars().nth(0).unwrap();

            if inner_i.starts_with(first_ch_j) {
                if inner_i == inner_j {
                    // println!("found {i}");
                    vec.push(i);
                    break;
                }
            }
        } //end inner for
    } //end top for
    // println!("{vec:#?}");

    vec.sort();
    vec.dedup();
    println!("Совпадений найденно: {}\n", vec.len());
    return vec;
}

async fn translate_(text: String) -> String {
    let ru = translate_from_english(&text, "ru").await.unwrap();
    let str = capitalize(format!("{text} — {ru}").to_string());
    println!("{str}");
    return str;
}

fn write_docx(texts: Vec<String>, output: String) -> Result<(), Box<dyn std::error::Error>> {
    if !Path::new(FILENAME).exists() {
        panic!("Не могу найти папку: {FILENAME}. Попробуйте создать её вручную возле .exe файла.")
    }

    let mut odt_file_name = output.clone();
    if odt_file_name.contains("docx") {
        odt_file_name = odt_file_name.replace("docx", "odt");
    } else {
        odt_file_name = odt_file_name.replace("doc", "odt");
    }
    let full_path = &format!("{FILENAME}/{odt_file_name}");
    let full_path_ouptup = &format!("{FILENAME}/{output}");

    let mut docx = Docx::default();
    for text in texts {
        let paragraph = Paragraph::default().push(Run::default().push_text(Text::from(text)));
        docx.document.push(paragraph);
    }
    docx.write_file(full_path_ouptup)?;
    #[cfg(target_os = "linux")]
    match convert_docx_to_odt(full_path_ouptup, full_path) {
        Ok(_) => {
            if Path::new(full_path).exists() {
                println!("Ваш .odt файл успешно создан\n")
            } else {
                println!(
                    "Не удалось создать .odt файл, вероятнее всего ваш дистрибутив исползует тругой офисный пакет (не libreoffice). Можете попробовать использовать .docx/.doc файл\n",
                )
            }
        }
        Err(_) => println!(
            "Не удалось создать .odt файл, вероятнее всего ваш дистрибутив исползует тругой офисный пакет (не libreoffice). Можете попробовать использовать .docx/.doc файл\n",
        ),
    };

    Ok(())
}

fn convert_docx_to_odt(
    input_path: &str,
    output_path: &str,
) -> Result<(), Box<dyn std::error::Error>> {
    let _ = Command::new("libreoffice")
        .arg("--headless")
        .arg("--convert-to")
        .arg("odt")
        .arg(input_path)
        .arg("--outdir")
        .arg(
            std::path::Path::new(output_path)
                .parent()
                .unwrap_or_else(|| std::path::Path::new(".")),
        ) // Ensure output directory exists
        .output();

    Ok(())
}

fn capitalize(s: String) -> String {
    let mut chars = s.chars();
    return match chars.next() {
        None => String::new(),
        Some(ch) => {
            format!(
                "{}{}",
                ch.to_uppercase().collect::<String>(),
                chars.as_str()
            )
        }
    };
}

fn mkdir(name: &str) -> std::io::Result<()> {
    fs::create_dir_all(name)?;
    Ok(())
}
