document.querySelector('.select-button').addEventListener('click', function () {
    const dropdown = document.querySelector('.dropdown');
    dropdown.classList.toggle('hidden'); // Hiện/ẩn dropdown
});

document.querySelector('.confirm-button').addEventListener('click', function () {
    const dropdown = document.querySelector('.dropdown');
    dropdown.classList.add('hidden'); // Ẩn dropdown
    updateButtonText();  // Cập nhật lại văn bản của nút khi xác nhận
});

document.querySelectorAll('.btn').forEach(button => {
    button.addEventListener('click', function () {
        const input = this.parentElement.querySelector('.number-input');
        let value = parseInt(input.value, 10);

        // Tăng hoặc giảm giá trị tuỳ theo nút bấm
        if (this.classList.contains('increase')) {
            input.value = value + 1;
        } else if (this.classList.contains('decrease')) {
            // Giảm giá trị nhưng không cho phép người lớn giảm xuống dưới 1
            if (input.id === 'adult-count' && value > 1) {
                input.value = value - 1;
            } else if (input.id !== 'adult-count' && value > 0) {
                input.value = value - 1;
            }
        }

        updateButtonText();  // Cập nhật lại nút sau mỗi lần thay đổi số lượng
    });
});

// Hàm cập nhật văn bản trên nút "Chọn số hành khách"
function updateButtonText() {
    let adultCount = parseInt(document.getElementById('adult-count').value) || 1;  // Mặc định là 1 người lớn
    let childCount = parseInt(document.getElementById('child-count').value) || 0;
    let infantCount = parseInt(document.getElementById('infant-count').value) || 0;
    let buttonText = "Chọn số hành khách";

    if (adultCount > 0 || childCount > 0 || infantCount > 0) {
        let adultText = adultCount === 1 ? "1 người lớn" : adultCount + " người lớn";
        let childText = childCount > 0 ? childCount + " trẻ em" : "";
        let infantText = infantCount > 0 ? infantCount + " em bé" : "";

        buttonText = adultText;
        if (childText) buttonText += ", " + childText;
        if (infantText) buttonText += ", " + infantText;
    }

    document.getElementById('select-button').textContent = buttonText;
}

// Khi trang tải, đảm bảo các giá trị ban đầu
window.onload = function() {
    // Đảm bảo giá trị mặc định
    document.getElementById('adult-count').value = 1;  // Mặc định 1 người lớn
    document.getElementById('child-count').value = 0;
    document.getElementById('infant-count').value = 0;
    updateButtonText();  // Cập nhật lại nút ngay khi trang tải
}

// Sự kiện focus để xóa giá trị nhập trong trường sân bay khi nhấn vào
document.getElementById('departure').addEventListener('focus', function() {
    this.value = '';
});

document.getElementById('arrival').addEventListener('focus', function() {
    this.value = '';
});



