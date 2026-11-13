/* So What? controls. Progressive: without this file every story is visible and readable. */
(function () {
  var $ = function (s, r) { return (r || document).querySelector(s) }
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)) }
  var state = { cat: 'all', ind: 'all', min: 3, india: false, cafe: false }
  try { var saved = JSON.parse(localStorage.getItem('sowhat') || '{}'); if (saved.cafe) state.cafe = true; if (saved.india) state.india = true } catch (e) {}

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
    document.body.classList.toggle('cafe', state.cafe)
    $$('[data-cat-btn]').forEach(function (b, i) {
      var on = b.dataset.catBtn === state.cat
      b.setAttribute('aria-pressed', on)
      if (on) { var dial = $('.dial'); if (dial) dial.style.transform = 'rotate(' + (i * 45) + 'deg)' }
    })
    $$('[data-ind-btn]').forEach(function (b) { b.setAttribute('aria-pressed', b.dataset.indBtn === state.ind) })
    $('#lens').setAttribute('aria-pressed', state.india)
    $('#cafe').setAttribute('aria-pressed', state.cafe)
    var out = $('#count'); if (out) out.textContent = shown + (shown === 1 ? ' story' : ' stories')
    try { localStorage.setItem('sowhat', JSON.stringify({ cafe: state.cafe, india: state.india })) } catch (e) {}
  }
  document.addEventListener('click', function (e) {
    var b = e.target.closest('[data-cat-btn]'); if (b) { state.cat = b.dataset.catBtn; apply(); return }
    b = e.target.closest('[data-ind-btn]'); if (b) { state.ind = b.dataset.indBtn; apply(); return }
    if (e.target.closest('#lens')) { state.india = !state.india; apply(); return }
    if (e.target.closest('#cafe')) { state.cafe = !state.cafe; apply(); return }
    var p = e.target.closest('.peak'); if (p) { var t = document.getElementById(p.dataset.for); if (t) { t.scrollIntoView({ block: 'center', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' }); var a = $('h3 a', t); if (a) a.focus({ preventScroll: true }) } }
  })
  document.addEventListener('keydown', function (e) {
    var p = e.target.closest && e.target.closest('.peak')
    if (p && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); p.dispatchEvent(new MouseEvent('click', { bubbles: true })) }
  })
  var range = $('#min'); if (range) range.addEventListener('input', function () { state.min = Number(range.value); $('#minval').textContent = range.value + '+'; apply() })
  apply()

  // Monday signup: posts to the lead sheet; falls back to WhatsApp when no endpoint is set
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
