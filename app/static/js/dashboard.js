// ダッシュボード専用JavaScript

document.addEventListener('DOMContentLoaded', function() {
  // カード要素のアニメーション
  const statCards = document.querySelectorAll('.stats-cards .card');
  statCards.forEach(function(card, index) {
    setTimeout(function() {
      card.classList.add('animate-fade-in');
    }, index * 100);
  });

  // クイックアクセスボタンのアニメーション
  const quickButtons = document.querySelectorAll('.row .btn-lg');
  quickButtons.forEach(function(button, index) {
    setTimeout(function() {
      button.classList.add('animate-fade-in');
    }, 500 + (index * 100));
  });

  // グラフ描画（Chart.jsが含まれている場合）
  if (typeof Chart !== 'undefined' && document.getElementById('reportChart')) {
    const ctx = document.getElementById('reportChart').getContext('2d');
    
    // サンプルデータ（実際の実装時にはバックエンドからデータを取得）
    const monthlyData = {
      labels: ['1月', '2月', '3月', '4月', '5月', '6月'],
      datasets: [
        {
          label: '完了報告書',
          data: [12, 19, 13, 15, 22, 27],
          backgroundColor: 'rgba(40, 167, 69, 0.2)',
          borderColor: 'rgba(40, 167, 69, 1)',
          borderWidth: 2,
          tension: 0.4
        },
        {
          label: '未完了報告書',
          data: [3, 5, 2, 4, 6, 3],
          backgroundColor: 'rgba(255, 193, 7, 0.2)',
          borderColor: 'rgba(255, 193, 7, 1)',
          borderWidth: 2,
          tension: 0.4
        }
      ]
    };
    
    const config = {
      type: 'line',
      data: monthlyData,
      options: {
        responsive: true,
        plugins: {
          legend: {
            position: 'top',
          },
          title: {
            display: true,
            text: '月別報告書作成数'
          }
        },
        scales: {
          y: {
            beginAtZero: true
          }
        }
      }
    };
    
    new Chart(ctx, config);
  }

  // サマリーカードのホバーエフェクト強化
  document.querySelectorAll('.stats-cards .card').forEach(card => {
    card.addEventListener('mouseenter', function() {
      this.querySelector('i').classList.add('fa-beat');
    });
    
    card.addEventListener('mouseleave', function() {
      this.querySelector('i').classList.remove('fa-beat');
    });
  });

  // ダッシュボード要素の自動更新（必要な場合）
  function refreshDashboardData() {
    // 実際の実装では非同期リクエストを行いダッシュボードデータを更新
    console.log('ダッシュボードデータを更新中...');
  }

  // 定期更新が必要な場合はコメントを解除
  // const refreshInterval = 60000; // 1分ごと
  // setInterval(refreshDashboardData, refreshInterval);

  // テーブル内の行にクリックイベントを追加
  const tableRows = document.querySelectorAll('tbody tr[data-href]');
  tableRows.forEach(function(row) {
    row.addEventListener('click', function() {
      window.location.href = this.getAttribute('data-href');
    });
    row.style.cursor = 'pointer';
  });

  // ページロード時のローディングインジケータ
  const pageLoader = document.getElementById('page-loader');
  if (pageLoader) {
    setTimeout(function() {
      pageLoader.classList.add('loaded');
      setTimeout(function() {
        pageLoader.style.display = 'none';
      }, 500);
    }, 300);
  }

  // ウィンドウサイズに応じてカードのレイアウトを調整
  function adjustLayout() {
    const isMobile = window.innerWidth < 768;
    const statsCards = document.querySelector('.stats-cards');
    
    if (statsCards) {
      const cards = statsCards.querySelectorAll('.card');
      cards.forEach(card => {
        // モバイル表示時の最適化
        if (isMobile) {
          card.classList.add('mb-3');
        } else {
          card.classList.remove('mb-3');
        }
      });
    }
  }
  
  // 初期調整
  adjustLayout();
  
  // リサイズ時にレイアウト調整
  window.addEventListener('resize', adjustLayout);
  
  // タッチデバイスでのインタラクション最適化
  const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
  
  if (isTouchDevice) {
    // クイックアクセスボタンのタッチフィードバック強化
    const quickButtons = document.querySelectorAll('.card-body a.btn');
    quickButtons.forEach(button => {
      button.addEventListener('touchstart', function() {
        this.style.transform = 'scale(0.97)';
      });
      
      button.addEventListener('touchend', function() {
        this.style.transform = 'scale(1)';
      });
    });
    
    // スライプでのナビゲーション
    let touchStartX = 0;
    let touchEndX = 0;
    
    document.addEventListener('touchstart', function(e) {
      touchStartX = e.changedTouches[0].screenX;
    }, false);
    
    document.addEventListener('touchend', function(e) {
      touchEndX = e.changedTouches[0].screenX;
      handleSwipe();
    }, false);
    
    function handleSwipe() {
      const swipeThreshold = 100; // スワイプと認識する最小距離
      
      if (touchEndX - touchStartX > swipeThreshold) {
        // 右スワイプ - 前のページに戻る
        const backLink = document.querySelector('.nav-back');
        if (backLink) {
          backLink.click();
        }
      }
    }
  }
}); 