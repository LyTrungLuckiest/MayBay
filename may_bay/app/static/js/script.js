function toggleReturnDate() {
    var checkBox = document.getElementById("roundTrip");
    var returnDateInput = document.getElementById("return_date");

    if (checkBox.checked) {
        returnDateInput.style.display = "block";
    } else {
        returnDateInput.style.display = "none";
    }
}


window.onload = function() {
    toggleReturnDate();
};


function addToCart(flight_id, plane_name, departure, arrival, day, type_ticket, price) {
    fetch('/api/carts', {
        method: "POST",
        body: JSON.stringify({
            "flight_id": flight_id,
            "plane_name": plane_name,
            "departure": departure,
            "arrival": arrival,
            "day": day,
            "type_ticket": type_ticket,
            "price": price
        }),
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(res => res.json())
      .then(data => {
          // Cập nhật số lượng hiển thị trên giao diện (biểu tượng giỏ hàng)
          let counters = document.getElementsByClassName("cart-counter");
          for (let c of counters)
              c.innerText = data.total_quantity;

          alert("Chuyến bay đã được thêm vào giỏ hàng!");
      })
      .catch(err => console.error("Error:", err));
}

//update cart
document.addEventListener('DOMContentLoaded', function () {
        const quantityInputs = document.querySelectorAll('input[type="number"]');

        quantityInputs.forEach(input => {
            input.addEventListener('change', function () {
                const row = input.closest('tr');
                const flight_id = row.querySelector('td:nth-child(1)').innerText.trim();
                const type_ticket = row.querySelector('td:nth-child(6)').innerText.trim();
                const new_quantity = parseInt(input.value);

                // Kiểm tra nếu số lượng mới hợp lệ
                if (new_quantity < 1) {
                    alert("Số lượng phải lớn hơn 0!");
                    input.value = 1; // Reset về 1 nếu sai
                    return;
                }

                // Gửi dữ liệu cập nhật lên server
                fetch('/cart/update', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        flight_id: flight_id,
                        type_ticket: type_ticket,
                        quantity: new_quantity
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Cập nhật lại tổng tiền và số lượng
                        const stats = data.stats;
                        document.querySelector('.alert-info h3:nth-child(1)').innerText =
                            `Tổng tiền: ${stats.total_price.toLocaleString()} VNĐ`;
                        document.querySelector('.alert-info h3:nth-child(2)').innerText =
                            `Tổng số lượng: ${stats.total_quantity}`;
                    } else {
                        alert('Có lỗi xảy ra khi cập nhật số lượng!');
                    }
                });
            });
        });
    });
//update cart


// delete data in cart
 document.addEventListener('DOMContentLoaded', function () {
        const deleteButtons = document.querySelectorAll('.btn-danger');

        deleteButtons.forEach(button => {
            button.addEventListener('click', function () {
                const row = button.closest('tr');
                const flight_id = row.querySelector('td:nth-child(1)').innerText.trim();
                const type_ticket = row.querySelector('td:nth-child(6)').innerText.trim();

                fetch('/cart/delete', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        flight_id: flight_id,
                        type_ticket: type_ticket
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Xóa hàng này khỏi bảng
                        row.remove();

                        // Cập nhật tổng tiền và số lượng
                        const stats = data.stats;
                        document.querySelector('.alert-info h3:nth-child(1)').innerText =
                            `Tổng tiền: ${stats.total_price.toLocaleString()} VNĐ`;
                        document.querySelector('.alert-info h3:nth-child(2)').innerText =
                            `Tổng số lượng: ${stats.total_quantity}`;
                    } else {
                        alert('Có lỗi xảy ra!');
                    }
                });
            });
        });
    });
// delete data in cart



function changeCity(cityName) {

  const currentScrollPosition = window.scrollY;


  const newUrl = "?departure=" + cityName;
  history.pushState(null, null, newUrl);


  const buttons = document.querySelectorAll('.btn-outline-primary');


  buttons.forEach(button => {
      button.classList.remove('active', 'btn-primary', 'text-white');
  });


  const selectedButton = document.querySelector(`a[onclick="changeCity('${cityName}')"]`);
  if (selectedButton) {
      selectedButton.classList.add('active', 'btn-primary', 'text-white');
  }


  fetch(newUrl)
      .then(response => response.text())
      .then(data => {

          const parser = new DOMParser();
          const doc = parser.parseFromString(data, 'text/html');
          const newRoutes = doc.querySelector('#routes-section');

          document.getElementById('routes-section').innerHTML = newRoutes.innerHTML;

          window.scrollTo(0, currentScrollPosition);
      })
      .catch(error => {
          console.error('Error fetching new data:', error);
      });
}