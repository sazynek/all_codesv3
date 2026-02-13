// Definition for singly-linked list.
#[derive(PartialEq, Eq, Clone, Debug)]
pub struct ListNode {
    pub val: i32,
    pub next: Option<Box<ListNode>>,
}

impl ListNode {
    #[inline]
    fn new(val: i32) -> Self {
        ListNode { next: None, val }
    }
}
struct Solution {}
impl Solution {
    pub fn merge_two_lists(
        &self,
        list1: Option<Box<ListNode>>,
        list2: Option<Box<ListNode>>,
    ) -> Option<Box<ListNode>> {
        return Some(Box::new(ListNode {
            val: 22,
            next: None,
        }));
    }
}

pub fn r6() {
    let sol = Solution {};
    let res = sol.merge_two_lists(list1, list2);
    println!("Result is {res:?}");
}
