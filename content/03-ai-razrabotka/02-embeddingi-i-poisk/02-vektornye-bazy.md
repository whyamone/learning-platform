---
title: Векторные базы данных
summary: Где хранить эмбеддинги и как быстро искать среди миллионов векторов.
goal: Сохранять документы с эмбеддингами в векторной базе и искать с фильтрами по метаданным.
estimated_hours: 8
stub: true
concepts:
  - векторный индекс
  - приближённый поиск ближайших соседей
  - метаданные и фильтры
  - коллекция
glossary:
  vector database: векторная база данных
  index: индекс
  nearest neighbor: ближайший сосед
  metadata: метаданные — сведения о документе
  collection: коллекция
links:
  - title: Документация Chroma
    url: https://docs.trychroma.com/
    kind: docs
    lang: en
  - title: Документация Qdrant
    url: https://qdrant.tech/documentation/
    kind: docs
    lang: en
  - title: pgvector — векторы в PostgreSQL
    url: https://github.com/pgvector/pgvector
    kind: docs
    lang: en
done_criteria:
  - Загрузил коллекцию документов в векторную базу
  - Выполняю поиск с фильтром по метаданным
  - Могу объяснить, когда хватит pgvector, а когда нужна отдельная база
---

# Практика

Перенеси поиск из прошлой темы в векторную базу (Chroma или Qdrant в Docker). Добавь к документам метаданные — раздел, дату — и поиск с фильтром. Измерь скорость на десяти тысячах документов.
