fn main() {
    let arr = [1, 2, 3, 4, 5];
    if arr.len() > 0 {
        let without_last = &arr[..arr.len() - 1];
        println!("{:?}", without_last); // [1, 2, 3, 4]
    }
}
