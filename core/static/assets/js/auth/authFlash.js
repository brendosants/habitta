export function initFlashMessages() {
  {% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
      {% for category, message in messages %}
        Swal.fire({
          toast: true,
          position: 'top-end',
          icon: '{{ category }}',
          title: '{{ message }}',
          showConfirmButton: false,
          timer: 5000,
          timerProgressBar: true
        });
      {% endfor %}
    {% endif %}
  {% endwith %}
}