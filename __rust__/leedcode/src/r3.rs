use std::collections::HashMap;

// use std::string::ToString;
struct Solution {}
impl Solution {
    pub fn roman_to_int(&self, s: String) -> i32 {
        let r2i = HashMap::from([
            ("I", 1),
            ("V", 5),
            ("X", 10),
            ("L", 50),
            ("C", 100),
            ("D", 500),
            ("M", 1000),
        ]);
        let mut strs = s.chars().map(|v| v.to_string()).collect::<Vec<String>>();
        strs.reverse();
        recurse(&mut strs, &r2i, 0)
    }
}

pub fn r3() {
    let sol = Solution {};

    let integer = sol.roman_to_int("MCMXCI".to_string());
    println!("Result: {integer}");
}

fn recurse(s: &mut Vec<String>, table: &HashMap<&str, i32>, mut value: i32) -> i32 {
    println!("{s:?}");
    if s.len() == 0 {
        return value;
    }
    if s.len() > 1 {
        let first = table[s.pop().unwrap().as_str()];
        let after_first = table[s.last().unwrap().as_str()];

        if first >= after_first {
            println!("{first}>{after_first}");

            value += first;
            return recurse(s, table, value);
        } else {
            println!("{first}<{after_first}");

            value += -first;
            return recurse(s, table, value);
        }
    } else {
        let first = table[s.pop().unwrap().as_str()];
        println!("last {first}");
        value += first;
        return recurse(s, table, value);
    }
}

// ------------------------------------------------------------------   Iteration alternative  ------------------------------------------------------------------

// impl Solution {
//     pub fn roman_to_int(s: String) -> i32 {
//         let map: std::collections::HashMap<char, i32> = [
//             ('I', 1),
//             ('V', 5),
//             ('X', 10),
//             ('L', 50),
//             ('C', 100),
//             ('D', 500),
//             ('M', 1000),
//         ].iter().cloned().collect();

//         let mut total = 0;
//         let mut prev = 0;

//         for c in s.chars().rev() {
//             let current = map[&c];
//             if current < prev {
//                 total -= current;
//             } else {
//                 total += current;
//             }
//             prev = current;
//         }

//         total
//     }
// }
