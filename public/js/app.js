(function () {
  const map = L.map('map', { zoomControl: true, minZoom: 5, maxZoom: 12 }).setView([48.5, 31.2], 6);
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Esri · DeepState-стиль · ukrainian_geodata',
    maxZoom: 12,
  }).addTo(map);

  const $info = document.getElementById('info');
  const $summary = document.getElementById('summary');

  // --- Геометрія-помічники ---
  function ringArea(coords) {
    let area = 0;
    for (let i = 0, len = coords.length, j = len - 1; i < len; j = i++) {
      const [x1, y1] = coords[i], [x2, y2] = coords[j];
      area += (x1 * y2 - x2 * y1);
    }
    return Math.abs(area) / 2;
  }
  function polygonArea(feature) {
    const g = feature.geometry;
    let total = 0;
    const polys = g.type === 'Polygon' ? [g.coordinates] : g.coordinates;
    for (const poly of polys) {
      total += ringArea(poly[0]);
      for (let h = 1; h < poly.length; h++) total -= ringArea(poly[h]);
    }
    return total;
  }
  function centroid(feature) {
    const polys = feature.geometry.type === 'Polygon' ? [feature.geometry.coordinates] : feature.geometry.coordinates;
    const ring = polys[0][0];
    let x = 0, y = 0;
    for (const [lx, ly] of ring) { x += lx; y += ly; }
    return [x / ring.length, y / ring.length];
  }
  function pointInPoly(pt, poly) {
    const ring = poly[0];
    let inside = false;
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      const [xi, yi] = ring[i], [xj, yj] = ring[j];
      if (((yi > pt[1]) !== (yj > pt[1])) && (pt[0] < (xj - xi) * (pt[1] - yi) / (yj - yi) + xi)) inside = !inside;
    }
    return inside;
  }

  function statusOf(regionName) {
    const d = window.OBLAST_DATA[regionName];
    return d ? d.status : 'liberated';
  }
  function styleFor(status, weight, fillOpacity) {
    const m = window.STATUS_META[status];
    return { color: m.color, weight, fillColor: m.fill, fillOpacity, dashArray: status === 'contested' ? '4 3' : null };
  }

  let oblasts, rayony, hromady;
  let oblastLayer, rayonLayer, hromadaLayer;

  Promise.all([
    fetch('data/regiony.geojson').then(r => r.json()),
    fetch('data/rayony.geojson').then(r => r.json()),
    fetch('data/hromady.geojson').then(r => r.json()),
  ]).then(([reg, ray, hro]) => {
    oblasts = reg; rayony = ray; hromady = hro;

    // Площі областей
    const oblastArea = {};
    oblasts.features.forEach(f => { oblastArea[f.properties.region] = polygonArea(f); });

    // Для районів визначити область через point-in-polygon (у rayony немає поля region)
    const rayonOblast = {};
    rayony.features.forEach(rf => {
      const c = centroid(rf);
      for (const of of oblasts.features) {
        const polys = of.geometry.type === 'Polygon' ? [of.geometry.coordinates] : of.geometry.coordinates;
        if (polys.some(p => pointInPoly(c, p))) { rayonOblast[rf.properties.fid] = of.properties.region; break; }
      }
    });

    // --- Шар областей ---
    oblastLayer = L.geoJSON(oblasts, {
      style: f => styleFor(statusOf(f.properties.region), 2, 0.35),
      onEachFeature: (f, layer) => {
        layer.on({ click: () => showOblast(f, layer), mouseover: () => layer.setStyle({ weight: 3 }), mouseout: () => layer.setStyle(styleFor(statusOf(f.properties.region), 2, 0.35)) });
      },
    }).addTo(map);

    // --- Шар районів ---
    rayonLayer = L.geoJSON(rayony, {
      style: f => {
        const ob = rayonOblast[f.properties.fid] || '';
        return styleFor(statusOf(ob), 1, 0.25);
      },
      onEachFeature: (f, layer) => {
        const ob = rayonOblast[f.properties.fid] || '';
        layer.on({ click: (e) => { L.DomEvent.stopPropagation(e); showRayon(f, ob); } });
      },
    });

    // --- Шар громад ---
    hromadaLayer = L.geoJSON(hromady, {
      style: f => styleFor(statusOf(f.properties.region), 0.6, 0.2),
      onEachFeature: (f, layer) => {
        layer.on({ click: (e) => { L.DomEvent.stopPropagation(e); showHromada(f); } });
      },
    });

    // Міста
    window.CITY_DATA.forEach(c => {
      const m = window.STATUS_META[c.status];
      L.circleMarker([c.lat, c.lng], {
        radius: 9, color: '#fff', weight: 2, fillColor: m.fill, fillOpacity: 0.95,
        bubblingMouseEvents: false,
      })
        .bindTooltip(`${c.name}`, { direction: 'top', offset: [0, -8] })
        .bindPopup(`<b>${c.name}</b><br><span class="pop">${window.fmt(c.pop2026)}</span> осіб (оцінка 2026)`)
        .on('click', (e) => { L.DomEvent.stopPropagation(e); })
        .addTo(map);
    });

    updateLayers();
    map.on('zoomend', updateLayers);
    renderSummary();
  });

  function updateLayers() {
    const z = map.getZoom();
    if (z >= 9) {
      if (!map.hasLayer(hromadaLayer)) map.addLayer(hromadaLayer);
      if (map.hasLayer(rayonLayer)) map.removeLayer(rayonLayer);
    } else if (z >= 7) {
      if (map.hasLayer(hromadaLayer)) map.removeLayer(hromadaLayer);
      if (!map.hasLayer(rayonLayer)) map.addLayer(rayonLayer);
    } else {
      if (map.hasLayer(rayonLayer)) map.removeLayer(rayonLayer);
      if (map.hasLayer(hromadaLayer)) map.removeLayer(hromadaLayer);
    }
  }

  function badge(status) {
    const m = window.STATUS_META[status];
    return `<span class="badge ${status}">${m.label}</span>`;
  }

  function showOblast(f) {
    const name = f.properties.region;
    const d = window.OBLAST_DATA[name];
    const p26 = window.pop2026(d);
    const occPop = Math.round(p26 * d.occupiedPct / 100);
    $info.innerHTML = `
      <h2>${name}</h2>
      <div class="row"><span>Статус</span><span class="v">${badge(d.status)}</span></div>
      <div class="row"><span>Населення 2021</span><span class="v">${window.fmt(d.pop2021)}</span></div>
      <div class="row"><span>Населення 2026 <i>(оц.)</i></span><span class="v">${window.fmt(p26)}</span></div>
      <div class="row"><span>Окуповано території</span><span class="v">${d.occupiedPct}%</span></div>
      <div class="row"><span>Населення під окупацією</span><span class="v">${window.fmt(occPop)}</span></div>`;
    map.fitBounds(oblastLayer.getLayers().find(l => l.feature === f).getBounds(), { padding: [40, 40] });
  }

  function showRayon(f, oblastName) {
    const ob = window.OBLAST_DATA[oblastName] || { pop2021: 0, factor: 0.8, status: 'liberated', occupiedPct: 0 };
    const obArea = polygonArea(oblasts.features.find(o => o.properties.region === oblastName));
    const rArea = polygonArea(f);
    const est = obArea > 0 ? Math.round(window.pop2026(ob) * rArea / obArea) : 0;
    $info.innerHTML = `
      <h2>${f.properties.rayon}</h2>
      <div class="row"><span>Область</span><span class="v">${oblastName || '—'}</span></div>
      <div class="row"><span>Статус</span><span class="v">${badge(ob.status)}</span></div>
      <div class="row"><span>Населення 2026 <i>(оц.)</i></span><span class="v">${window.fmt(est)}</span></div>`;
  }

  function showHromada(f) {
    const p = f.properties;
    const ob = window.OBLAST_DATA[p.region] || { pop2021: 0, factor: 0.8, status: 'liberated', occupiedPct: 0 };
    const obArea = polygonArea(oblasts.features.find(o => o.properties.region === p.region));
    const hArea = polygonArea(f);
    const est = obArea > 0 ? Math.round(window.pop2026(ob) * hArea / obArea) : 0;
    $info.innerHTML = `
      <h2>${p.hromada}</h2>
      <div class="row"><span>Район</span><span class="v">${p.rayon}</span></div>
      <div class="row"><span>Область</span><span class="v">${p.region}</span></div>
      <div class="row"><span>Статус</span><span class="v">${badge(ob.status)}</span></div>
      <div class="row"><span>Населення 2026 <i>(оц.)</i></span><span class="v">${window.fmt(est)}</span></div>`;
  }

  function renderSummary() {
    let total = 0, occ = 0, occPop = 0;
    for (const name in window.OBLAST_DATA) {
      const d = window.OBLAST_DATA[name];
      const p = window.pop2026(d);
      total += p;
      if (d.status === 'occupied') { occ += p; occPop += Math.round(p * d.occupiedPct / 100); }
    }
    $summary.innerHTML = `
      <h3>Підсумок по Україні</h3>
      <div class="row"><span>Населення 2026 (оц.)</span><span>${window.fmt(total)}</span></div>
      <div class="row"><span>В окупованих областях</span><span>${window.fmt(occ)}</span></div>
      <div class="row"><span>Під окупацією РФ</span><span>${window.fmt(occPop)}</span></div>`;
  }

  map.on('click', () => {
    $info.innerHTML = `<p class="hint">Натисніть на область, район чи громаду, щоб побачити орієнтовне населення на 2026 рік.</p>`;
  });
})();
