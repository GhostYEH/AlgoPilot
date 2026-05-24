#include <iostream>
#include <vector>
#include <unordered_map>

using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    if (!(cin >> n)) return 0;

    vector<int> nums(n);
    for (int i = 0; i < n; ++i) {
        cin >> nums[i];
    }

    int target;
    cin >> target;

    unordered_map<int, int> num_map;

    for (int i = 0; i < n; ++i) {
        int complement = target - nums[i];

        if (num_map.find(complement) != num_map.end()) {
            cout << num_map[complement] << " " << i << "\n";
            return 0;
        }

        num_map[nums[i]] = i;
    }

    return 0;
}
