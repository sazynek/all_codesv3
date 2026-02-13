struct Solution {}

impl Solution {
    pub fn is_valid(&self, s: String) -> bool {
        let mut stack: Vec<String> = Vec::new();

        let els = s
            .chars()
            .into_iter()
            .map(|f| f.to_string())
            .collect::<Vec<String>>();
        if els.len() == 1 {
            return false;
        }
        for i in els {
            if !stack.is_empty() {
                let first = stack.last().unwrap().to_string();

                if is_right_brace(&i) {
                    let reversed_first = mirror(&first);
                    println!("right brace reversed={reversed_first} i={i}");
                    if reversed_first == i {
                        println!("{first} and {i} == {}", reversed_first == i);
                        stack.pop();
                        // stack.pop();
                    } else {
                        return false;
                    }
                } else {
                    // left brace
                    stack.push(i);
                }
            } else {
                stack.push(i);
            }
        }
        println!("{stack:?}");
        if !stack.is_empty() {
            return false;
        }
        return true;
    }
}

pub fn r5() {
    let sol = Solution {};
    let res = sol.is_valid("(){[]}[".to_string());
    println!("Result is {res:?}");
}

fn is_right_brace(brace: &str) -> bool {
    match brace {
        "]" => true,
        ")" => true,
        "}" => true,
        _ => false,
    }
}
fn mirror(str: &str) -> String {
    match str {
        "[" => "]",
        "]" => "[",

        "(" => ")",
        ")" => "(",

        "{" => "}",
        "}" => "{",

        _ => panic!("error"),
    }
    .to_string()
}
