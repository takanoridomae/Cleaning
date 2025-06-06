// メインJavaScriptファイル

document.addEventListener('DOMContentLoaded', function() {
  // ツールチップの初期化
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function(tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // フラッシュメッセージの自動非表示
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(function(alert) {
    setTimeout(function() {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    }, 5000);
  });

  // 確認ダイアログ
  const confirmButtons = document.querySelectorAll('[data-confirm]');
  confirmButtons.forEach(function(button) {
    button.addEventListener('click', function(e) {
      if (!confirm(this.getAttribute('data-confirm'))) {
        e.preventDefault();
      }
    });
  });

  // 動的フォームバリデーション
  const forms = document.querySelectorAll('.needs-validation');
  Array.from(forms).forEach(function(form) {
    form.addEventListener('submit', function(event) {
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
      }
      form.classList.add('was-validated');
    }, false);
  });

  // データテーブルの初期化（データテーブルJSが含まれている場合）
  if (typeof $.fn.DataTable !== 'undefined') {
    $('.data-table').DataTable({
      language: {
        url: '//cdn.datatables.net/plug-ins/1.10.25/i18n/Japanese.json'
      },
      responsive: true,
      dom: "<'row'<'col-sm-12 col-md-6'l><'col-sm-12 col-md-6'f>>" +
           "<'row'<'col-sm-12'tr>>" +
           "<'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7'p>>",
    });
  }

  // ページ遷移後のスムーススクロール
  if (window.location.hash) {
    const targetElement = document.querySelector(window.location.hash);
    if (targetElement) {
      setTimeout(function() {
        window.scrollTo({
          top: targetElement.offsetTop - 70,
          behavior: 'smooth'
        });
      }, 100);
    }
  }

  // 日付選択の初期化（フラットピッカーJSが含まれている場合）
  if (typeof flatpickr !== 'undefined') {
    flatpickr('.date-picker', {
      dateFormat: 'Y-m-d',
      locale: 'ja',
      allowInput: true
    });
  }

  // 画像プレビュー表示
  const imageInputs = document.querySelectorAll('.image-input');
  imageInputs.forEach(function(input) {
    input.addEventListener('change', function() {
      const previewId = this.getAttribute('data-preview');
      const preview = document.getElementById(previewId);
      
      if (preview && this.files && this.files[0]) {
        const reader = new FileReader();
        
        reader.onload = function(e) {
          preview.src = e.target.result;
          preview.style.display = 'block';
        };
        
        reader.readAsDataURL(this.files[0]);
      }
    });
  });

  // スライドインアニメーション
  const animateItems = document.querySelectorAll('.animate-fade-in');
  animateItems.forEach(function(item, index) {
    item.style.animationDelay = (index * 0.1) + 's';
  });

  // レスポンシブテーブル処理
  const tables = document.querySelectorAll('table:not(.no-responsive)');
  tables.forEach(function(table) {
    if (!table.parentElement.classList.contains('table-responsive')) {
      const wrapper = document.createElement('div');
      wrapper.className = 'table-responsive';
      table.parentNode.insertBefore(wrapper, table);
      wrapper.appendChild(table);
    }
  });

  // Bootstrap のポップオーバーを初期化
  const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
  popoverTriggerList.map(function (popoverTriggerEl) {
    return new bootstrap.Popover(popoverTriggerEl);
  });

  // モバイルデバイス用のナビゲーション最適化
  const navbarToggler = document.querySelector('.navbar-toggler');
  const navbarLinks = document.querySelectorAll('.navbar-nav .nav-link');

  if (navbarToggler && navbarLinks.length > 0) {
    navbarLinks.forEach(link => {
      link.addEventListener('click', () => {
        // 小さい画面でメニューアイテムをクリックした時にメニューを閉じる
        if (window.innerWidth < 992 && document.querySelector('.navbar-collapse.show')) {
          navbarToggler.click();
        }
      });
    });
  }

  // タッチデバイス検出
  const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0 || navigator.msMaxTouchPoints > 0;
  if (isTouchDevice) {
    document.body.classList.add('touch-device');
  }

  // 日付入力フィールドの拡張
  const dateInputs = document.querySelectorAll('input[type="date"]');
  dateInputs.forEach(input => {
    // モバイルデバイスでは日付選択UIが提供されるのでそのまま使用
    if (!isTouchDevice) {
      // デスクトップでより良い日付選択UI実装を適用できる
      // 例: datepickerライブラリ等を使う場合はここに実装
    }
  });

  // 写真アップロードのプレビュー機能
  const photoInputs = document.querySelectorAll('input[type="file"][accept*="image"]');
  photoInputs.forEach(input => {
    input.addEventListener('change', function() {
      const previewContainer = this.closest('.form-group').querySelector('.preview-container');
      if (!previewContainer) return;
      
      previewContainer.innerHTML = '';
      
      if (this.files && this.files.length > 0) {
        for (let i = 0; i < this.files.length; i++) {
          const file = this.files[i];
          if (file.type.match('image.*')) {
            const reader = new FileReader();
            reader.onload = function(e) {
              const preview = document.createElement('div');
              preview.className = 'preview-item';
              preview.innerHTML = `
                <img src="${e.target.result}" alt="プレビュー" class="img-thumbnail">
                <p class="small text-muted mt-1">${file.name}</p>
              `;
              previewContainer.appendChild(preview);
            }
            reader.readAsDataURL(file);
          }
        }
      }
    });
  });
});

/**
 * 地図表示機能
 */
function showMapForAddress(address) {
    if (!address || address.trim() === '' || address.trim() === '未設定') {
        alert('住所が設定されていません。');
        return;
    }
    
    // 郵便番号記号を除去して住所を整形
    const cleanAddress = address.replace(/^〒\d{3}-?\d{4}\s*/, '').trim();
    
    if (cleanAddress === '') {
        alert('有効な住所が設定されていません。');
        return;
    }
    
    // GoogleマップのURLを生成（検索クエリとして住所を渡す）
    const mapUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(cleanAddress)}`;
    
    // 新しいタブでGoogleマップを開く
    window.open(mapUrl, '_blank', 'noopener,noreferrer');
} 