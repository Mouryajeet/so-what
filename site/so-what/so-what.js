/* So What? controls + the signal line's motion.
   Progressive: without this file every story and every peak is visible, readable and linked.
   Motion only runs when the reader hasn't asked for reduced motion. */
(function () {
  var $ = function (s, r) { return (r || document).querySelector(s) }
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)) }
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches
  var state = { cat: 'all', ind: 'all', min: 3, india: false, cafe: false }
  try { var saved = JSON.parse(localStorage.getItem('sowhat') || '{}'); if (saved.cafe) state.cafe = true } catch (e) {}

  var total = $$('.story').length

  /* ---------- filters ---------- */
  function apply() {
    var shown = 0
    $$('.story').forEach(function (el) {
      var ok = (state.cat === 'all' || el.dataset.cat === state.cat) &&
        (state.ind === 'all' || (el.dataset.ind || '').split('|').indexOf(state.ind) > -1) &&
        Number(el.dataset.imp) >= state.min && (!state.india || el.dataset.india === '1')
      el.hidden = !ok
      if (ok) shown++
    })
    $$('.day').forEach(function (d) {
      var any = $$('.story', d).some(function (s) { return !s.hidden })
      var msg = $('.empty', d)
      if (msg) msg.hidden = any
    })
    // peaks of filtered-out stories dim, so the line always matches the list
    $$('.peak, .mdot').forEach(function (p) {
      var t = document.getElementById(p.dataset.for)
      p.classList.toggle('off', !t || t.hidden)
    })
    document.body.classList.toggle('cafe', state.cafe)
    $$('[data-cat-btn]').forEach(function (b, i) {
      var on = b.dataset.catBtn === state.cat
      b.setAttribute('aria-pressed', on)
      if (on) { var dial = $('.dial'); if (dial) dial.style.transform = 'rotate(' + (i * 45) + 'deg)' }
    })
    $$('[data-ind-btn]').forEach(function (b) { b.setAttribute('aria-pressed', b.dataset.indBtn === state.ind) })
    $('#lens').setAttribute('aria-pressed', state.india)
    $('#cafe').setAttribute('aria-pressed', state.cafe)
    var filtered = state.cat !== 'all' || state.ind !== 'all' || state.min > 3 || state.india
    var out = $('#count')
    if (out) out.textContent = filtered ? 'Showing ' + shown + ' of ' + total + ' stories' : total + (total === 1 ? ' story' : ' stories')
    var clr = $('#clear'); if (clr) clr.hidden = !filtered
    try { localStorage.setItem('sowhat', JSON.stringify({ cafe: state.cafe })) } catch (e) {}
    if (sync) sync()
  }
  function clearFilters() {
    state.cat = 'all'; state.ind = 'all'; state.min = 3; state.india = false
    var r = $('#min'); if (r) { r.value = 3; $('#minval').textContent = '3+' }
    apply()
  }
  function goTo(id) {
    var t = document.getElementById(id); if (!t) return
    if (t.hidden) clearFilters()
    t.classList.remove('pre')
    t.scrollIntoView({ block: 'center', inline: 'start', behavior: reduce ? 'auto' : 'smooth' })
    var a = $('h3 a', t); if (a) a.focus({ preventScroll: true })
  }
  document.addEventListener('click', function (e) {
    var b = e.target.closest('[data-cat-btn]'); if (b) { state.cat = b.dataset.catBtn; apply(); return }
    b = e.target.closest('[data-ind-btn]'); if (b) { state.ind = b.dataset.indBtn; apply(); return }
    if (e.target.closest('#lens')) { state.india = !state.india; apply(); return }
    if (e.target.closest('#cafe')) { state.cafe = !state.cafe; apply(); return }
    if (e.target.closest('#clear')) { clearFilters(); return }
    var p = e.target.closest('.peak, .mdot'); if (p) goTo(p.dataset.for)
  })
  var range = $('#min'); if (range) range.addEventListener('input', function () { state.min = Number(range.value); $('#minval').textContent = range.value + '+'; apply() })

  /* ---------- the signal ---------- */
  var sig = $('.signal'), sync = null
  if (sig) {
    var W = +sig.dataset.w, VH = +sig.dataset.vh, B = +sig.dataset.base
    var peaks = $$('.peak', sig).map(function (el) { return { el: el, x: +el.dataset.x, h: +el.dataset.h, cur: +el.dataset.h, id: el.dataset.for } })
    var paths = $$('svg path', sig), grad = $('#sp'), head = $('.head', sig)
    var build = function () {
      var d = 'M0 ' + B
      peaks.forEach(function (p) { d += ' L' + (p.x - 26) + ' ' + B + ' L' + p.x + ' ' + (B - p.cur).toFixed(1) + ' L' + (p.x + 26) + ' ' + B })
      return d + ' L' + W + ' ' + B
    }
    var yAt = function (x) {
      for (var i = 0; i < peaks.length; i++) { var p = peaks[i]; if (x >= p.x - 26 && x <= p.x + 26) return B - p.cur * (1 - Math.abs(x - p.x) / 26) }
      return B
    }
    var draw = function () {
      var d = build(); paths.forEach(function (el) { el.setAttribute('d', d) })
      peaks.forEach(function (p) { p.el.style.top = ((B - p.cur) / VH * 100) + '%' })
    }
    var spark = function (px) {
      grad.setAttribute('x1', px - 300); grad.setAttribute('x2', px + 34)
      head.style.left = (px / W * 100) + '%'; head.style.top = (yAt(px) / VH * 100) + '%'
    }
    var easeIO = function (t) { return t < .5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2 }
    var back = function (t) { var c = 1.9; return 1 + (c + 1) * Math.pow(t - 1, 3) + c * Math.pow(t - 1, 2) }

    /* A pulse runs along the line. On the first run the peaks rise as it passes; after that it rides over them. */
    var inView = true, busy = false, timer = 0
    function run(intro) {
      if (busy) return
      busy = true; head.classList.add('on')
      var dur = intro ? 2300 : 2000, t0 = null, rise = 650
      peaks.forEach(function (p) { p.hit = null })
      function frame(ts) {
        if (t0 === null) t0 = ts
        var t = Math.min(1, (ts - t0) / dur), px = -120 + (W + 240) * easeIO(t), pending = false
        peaks.forEach(function (p) {
          if (p.hit === null && px >= p.x - 8) { p.hit = ts; p.el.classList.remove('pre'); p.el.classList.add('ping'); setTimeout(function () { p.el.classList.remove('ping') }, 750) }
          if (intro) {
            var k = p.hit === null ? 0 : Math.min(1, (ts - p.hit) / rise)
            p.cur = p.h * (k === 0 ? 0 : back(k))
            if (k < 1) pending = true
          }
        })
        if (intro) draw()
        spark(px)
        if (t < 1 || pending) requestAnimationFrame(frame)
        else { busy = false; head.classList.remove('on'); spark(-1000); if (intro) { peaks.forEach(function (p) { p.cur = p.h }); draw() } schedule() }
      }
      requestAnimationFrame(frame)
    }
    function schedule() {
      clearTimeout(timer)
      timer = setTimeout(function () { if (inView && !document.hidden) run(false); else schedule() }, 5200)
    }

    if (!reduce) {
      peaks.forEach(function (p) { p.cur = 0; p.el.classList.add('pre') })
      draw(); spark(-1000)
      sig.classList.add('ready')
      var started = false
      var io = new IntersectionObserver(function (es) {
        inView = es[0].isIntersecting
        if (inView && !started) { started = true; setTimeout(function () { run(true) }, 350) }
      })
      io.observe(sig)
    } else sig.classList.add('ready')

    /* Hover a story → its peak lights. */
    document.addEventListener('pointerover', function (e) {
      var s = e.target.closest && e.target.closest('.story'), id = s && s.id
      peaks.forEach(function (p) { p.el.classList.toggle('hover', p.id === id) })
    })

    /* ---------- mini signal: follows you down the page and marks the story you're reading ---------- */
    var today = $('.day.today'), list = today && $('.list', today)
    if (today) {
      var mini = document.createElement('div'); mini.className = 'mini'; mini.setAttribute('aria-hidden', 'true')
      var finalD = (function () { var keep = peaks.map(function (p) { return p.cur }); peaks.forEach(function (p) { p.cur = p.h }); var d = build(); peaks.forEach(function (p, i) { p.cur = keep[i] }); return d })()
      mini.innerHTML = '<div class="wrap"><span class="label mlab">Today’s signal</span><div class="mtrack"><svg viewBox="0 0 ' + W + ' ' + VH + '" preserveAspectRatio="none"><path d="' + finalD + '" fill="none" stroke="url(#sg)" stroke-width="1.5" vector-effect="non-scaling-stroke"/></svg>' +
        peaks.map(function (p) { return '<span class="mdot' + (p.el.classList.contains('hot') ? ' hot' : '') + '" data-for="' + p.id + '" style="left:' + (p.x / W * 100) + '%;top:' + ((B - p.h) / VH * 100) + '%"></span>' }).join('') +
        '</div><span class="label mcount"></span></div>'
      document.body.appendChild(mini)
      var mdots = $$('.mdot', mini), mcount = $('.mcount', mini)
      var queued = false, lastId = null
      sync = function () {
        if (queued) return; queued = true
        requestAnimationFrame(function () {
          queued = false
          var vh = innerHeight, nav = 72, sr = sig.getBoundingClientRect(), tr = today.getBoundingClientRect()
          var on = sr.bottom < nav + 10 && tr.top < vh * .6 && tr.bottom > nav + 120
          document.body.classList.toggle('mini-on', on)
          var stories = $$('.story', list).filter(function (s) { return !s.hidden }), best = null, bestD = 1e9
          var horiz = list.scrollWidth > list.clientWidth + 4
          var lr = list.getBoundingClientRect()
          stories.forEach(function (s) {
            var r = s.getBoundingClientRect(), dd
            if (horiz) { if (lr.top > vh || lr.bottom < 0) return; dd = Math.abs((r.left + Math.min(r.width, lr.width) / 2) - (lr.left + lr.width * .44)) }
            else { if (r.bottom < nav || r.top > vh) return; dd = Math.abs((r.top + r.bottom) / 2 - vh * .45) }
            if (dd < bestD) { bestD = dd; best = s }
          })
          var id = best ? best.id : null
          if (id === lastId) return
          lastId = id
          $$('.story.cur').forEach(function (s) { s.classList.remove('cur') })
          if (best) best.classList.add('cur')
          peaks.forEach(function (p) { p.el.classList.toggle('cur', p.id === id) })
          mdots.forEach(function (m) { m.classList.toggle('cur', m.dataset.for === id) })
          var i = stories.indexOf(best)  // reading position in the list, not the story's place on the line
          mcount.textContent = i > -1 ? String(i + 1).padStart(2, '0') + ' / ' + String(stories.length).padStart(2, '0') : ''
        })
      }
      addEventListener('scroll', sync, { passive: true })
      addEventListener('resize', sync, { passive: true })
      if (list) list.addEventListener('scroll', sync, { passive: true })
    }
  }

  /* ---------- stories drop in as they arrive on screen ---------- */
  if (!reduce && 'IntersectionObserver' in window) {
    var vw = innerWidth, vh0 = innerHeight
    var pre = $$('.story').filter(function (s) { var r = s.getBoundingClientRect(); return r.top > vh0 || r.left > vw })
    pre.forEach(function (s) { s.classList.add('pre') })
    var batch = 0
    var dio = new IntersectionObserver(function (es) {
      batch = 0
      es.forEach(function (en) {
        if (!en.isIntersecting) return
        var s = en.target; dio.unobserve(s)
        s.style.transitionDelay = (batch++ * 70) + 'ms'
        s.classList.remove('pre'); s.classList.add('flash')
        setTimeout(function () { s.style.transitionDelay = ''; s.classList.remove('flash') }, 1400)
      })
    }, { rootMargin: '0px 0px -8% 0px' })
    pre.forEach(function (s) { dio.observe(s) })
  }

  apply()

  /* ---------- Monday signup: posts to the lead sheet; falls back to WhatsApp when no endpoint is set ---------- */
  var form = $('#signup')
  if (form) form.addEventListener('submit', function (e) {
    e.preventDefault()
    var st = $('#status'), f = new FormData(form)
    var name = (f.get('name') || '').trim(), contact = (f.get('contact') || '').trim()
    if (!name || !contact) { st.textContent = 'Please add your name and a phone number or email.'; return }
    if (!f.get('consent')) { st.textContent = 'Please tick the box so we can send it to you.'; return }
    if (window.fbq) try { window.fbq('track', 'Lead', { content_name: 'so_what_signup' }) } catch (err) {}
    var url = form.dataset.endpoint
    if (!url) {
      var msg = 'Hi Brandmizer, please add me to So What? every Monday. Name: ' + name + '. Contact: ' + contact
      window.location.href = 'https://wa.me/' + form.dataset.wa + '?text=' + encodeURIComponent(msg)
      return
    }
    st.textContent = 'Sending…'
    fetch(url, { method: 'POST', mode: 'no-cors', body: new URLSearchParams({ name: name, contact: contact, consent: 'yes', page: location.pathname, at: new Date().toISOString() }) })
      .then(function () { st.textContent = 'Done. You’re on the list for Monday.'; form.reset() })
      .catch(function () { st.textContent = 'That didn’t go through. Please try again, or message us on WhatsApp.' })
  })
})()
