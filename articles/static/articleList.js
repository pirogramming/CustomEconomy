
  const selectEl = document.getElementById("sortSelect");
  const cardsEl = document.getElementById("articleCards");

  function escapeHtml(str) {
    if (!str) return "";
    return str.replaceAll("&", "&amp;")
              .replaceAll("<", "&lt;")
              .replaceAll(">", "&gt;")
              .replaceAll('"', "&quot;")
              .replaceAll("'", "&#039;");
  }

  function renderCards(articles) {
    cardsEl.innerHTML = articles.map(a => {
      const img = a.image_url
        ? `<img class="thumb" src="${escapeHtml(a.image_url)}" alt="">`
        : "";

      const desc = a.description ? escapeHtml(a.description) : "";

      return `
        <div class="article-card">
          ${img}
          <div class="article-info">
            <h3>${escapeHtml(a.title)}</h3>
            <p>${desc}</p>
          </div>
        </div>
      `;
    }).join("");
  }

  async function loadArticles(sortValue) {
    const res = await fetch(`/api/articles/articleList/?sort=${encodeURIComponent(sortValue)}`);
    if (!res.ok) {
      cardsEl.innerHTML = "<p>불러오기 실패 😵</p>";
      return;
    }
    const data = await res.json();
    renderCards(data.results);
  }

  // 최초 로딩
  loadArticles(selectEl.value);

  // 정렬 변경 시
  selectEl.addEventListener("change", (e) => {
    loadArticles(e.target.value);
  });
