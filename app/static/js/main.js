// エアコンクリーニング完了報告書システム - メインJavaScript

document.addEventListener('DOMContentLoaded', function() {
  // Bootstrap ツールチップの初期化
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

  // iOS デバイス検出とクラス追加
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
  if (isIOS) {
    document.body.classList.add('ios-device');
  }

  // タッチデバイス検出
  const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
  if (isTouchDevice) {
    document.body.classList.add('touch-device');
  }

  // モバイルナビゲーション最適化
  const navbarToggler = document.querySelector('.navbar-toggler');
  const navbarLinks = document.querySelectorAll('.navbar-nav .nav-link:not(.dropdown-toggle)');

  if (navbarToggler && navbarLinks.length > 0) {
    navbarLinks.forEach(link => {
      link.addEventListener('click', () => {
        if (window.innerWidth < 992 && document.querySelector('.navbar-collapse.show')) {
          navbarToggler.click();
        }
      });
    });
  }

  // iPhone専用ドロップダウン対応
  if (isIOS) {
    console.log('iOS デバイスが検出されました - 専用対応を実装');
    
    const dropdownToggles = document.querySelectorAll('.navbar-nav .dropdown-toggle');
    
         dropdownToggles.forEach((toggle, index) => {
       console.log(`iOS用ドロップダウン ${index + 1} を初期化`);
       
       // Bootstrap のイベントを無効化
       toggle.removeAttribute('data-bs-toggle');
       
       // カスタムタッチイベント
       toggle.addEventListener('touchstart', function(e) {
         e.preventDefault();
         e.stopPropagation();
         
         // ハンバーガーメニューが閉じている場合は開く
         const navbarCollapse = document.querySelector('.navbar-collapse');
         if (navbarCollapse && !navbarCollapse.classList.contains('show')) {
           console.log('ハンバーガーメニューが閉じているため開きます');
           navbarCollapse.classList.add('show');
         }
         
         const dropdown = this.closest('.dropdown');
         const menu = dropdown.querySelector('.dropdown-menu');
         const isOpen = dropdown.classList.contains('show');
         
         console.log(`iOS ドロップダウン ${index + 1} タッチ - 現在の状態: ${isOpen ? '開' : '閉'}`);
         
         // 全てのドロップダウンを閉じる
         document.querySelectorAll('.navbar-nav .dropdown').forEach(dd => {
           dd.classList.remove('show');
           dd.querySelector('.dropdown-menu').classList.remove('show');
           dd.querySelector('.dropdown-toggle').setAttribute('aria-expanded', 'false');
         });
         
         // 現在のドロップダウンが閉じていた場合は開く
         if (!isOpen) {
           dropdown.classList.add('show');
           menu.classList.add('show');
           this.setAttribute('aria-expanded', 'true');
           
           // デバッグ情報を出力
           console.log(`iOS ドロップダウン ${index + 1} を開きました`);
           console.log('ドロップダウン要素:', dropdown);
           console.log('メニュー要素:', menu);
           console.log('showクラス追加後:', dropdown.classList.contains('show'));
           console.log('メニューの表示状態:', window.getComputedStyle(menu).display);
           console.log('メニューのvisibility:', window.getComputedStyle(menu).visibility);
           console.log('メニューのopacity:', window.getComputedStyle(menu).opacity);
           
           // 強制的にスタイルを適用
           menu.style.display = 'block';
           menu.style.visibility = 'visible';
           menu.style.opacity = '1';
           menu.style.position = 'static';
           menu.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
           menu.style.border = '1px solid rgba(255, 255, 255, 0.2)';
           menu.style.borderRadius = '0.5rem';
           menu.style.padding = '0.5rem';
           menu.style.marginTop = '0.5rem';
           
           console.log('強制スタイル適用後のdisplay:', menu.style.display);
           
           // ドロップダウンアイテムにクリックイベントを追加
           const dropdownItems = menu.querySelectorAll('.dropdown-item');
           dropdownItems.forEach((item, itemIndex) => {
             console.log(`iOS ドロップダウンアイテム ${itemIndex + 1} にイベントを追加`);
             
             // 既存のイベントリスナーを削除（重複防止）
             item.removeEventListener('touchstart', handleDropdownItemTouch);
             item.removeEventListener('click', handleDropdownItemClick);
             
             // 新しいイベントリスナーを追加
             item.addEventListener('touchstart', handleDropdownItemTouch, { passive: false });
             item.addEventListener('click', handleDropdownItemClick);
           });
         }
       }, { passive: false });
     });
     
     // ドロップダウンアイテムのタッチハンドラ
     function handleDropdownItemTouch(e) {
       e.stopPropagation(); // ドロップダウンを閉じるイベントを防止
       const href = this.getAttribute('href');
       console.log('iOS ドロップダウンアイテムがタッチされました:', href);
       
       if (href && href !== '#') {
         console.log('ページ遷移を実行:', href);
         window.location.href = href;
       }
     }
     
     // ドロップダウンアイテムのクリックハンドラ
     function handleDropdownItemClick(e) {
       e.stopPropagation(); // ドロップダウンを閉じるイベントを防止
       const href = this.getAttribute('href');
       console.log('iOS ドロップダウンアイテムがクリックされました:', href);
       
       if (href && href !== '#') {
         console.log('ページ遷移を実行:', href);
         window.location.href = href;
       }
     }
    
         // iOS用外部タップ検出
     document.addEventListener('touchstart', function(e) {
       // ドロップダウンアイテムがタッチされた場合は閉じない
       if (e.target.classList.contains('dropdown-item')) {
         console.log('iOS: ドロップダウンアイテムがタッチされたため閉じません');
         return;
       }
       
       if (!e.target.closest('.navbar-nav .dropdown')) {
         console.log('iOS: ドロップダウン外をタッチ - 全て閉じます');
         document.querySelectorAll('.navbar-nav .dropdown.show').forEach(dropdown => {
           dropdown.classList.remove('show');
           dropdown.querySelector('.dropdown-menu').classList.remove('show');
           dropdown.querySelector('.dropdown-toggle').setAttribute('aria-expanded', 'false');
         });
       }
     });
  } else {
    console.log('非iOS デバイス - Bootstrap標準機能を使用');
    // 非iOSデバイスはBootstrapの標準機能を使用
  }
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