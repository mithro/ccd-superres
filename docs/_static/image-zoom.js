/*
 * Click-to-zoom for every image and flow chart in the documentation.
 *
 * Loaded on every page from docs/conf.py, so it needs no markup in the pages
 * themselves: any image added to any page later gets it automatically.
 *
 * Clicking a picture (or pressing Enter on it) opens it in a viewer that
 * fills the window. Inside the viewer: scroll or pinch to zoom, drag to
 * move, click to switch between whole-picture and close-up, Escape to close.
 */
(function () {
  "use strict";

  var CONTENT = "article[role=main], div[role=main], main article, article";
  var IMG = "img";
  var CHART = "pre.mermaid > svg, div.mermaid > svg";
  var MAX_ZOOM = 16; // times the size that fits the window
  var CLICK_ZOOM = 3;

  var overlay, stage, caption, level;
  var item = null; // the element shown in the viewer
  var opener = null; // the element on the page that was clicked
  var base = { w: 0, h: 0 }; // size at which the picture fits the window
  var view = { zoom: 1, x: 0, y: 0 }; // x, y: top left corner inside the stage
  var pointers = new Map();
  var gesture = null;
  var savedOverflow = "";

  /* ---- Finding the pictures on the page ---------------------------- */

  function zoomTarget(node) {
    if (!(node instanceof Element)) return null;
    var el = node.closest(IMG) || node.closest(CHART);
    if (!el || !el.closest(CONTENT) || el.closest(".image-zoom-overlay")) return null;
    // Not pictures: the small open/close arrows Sphinx puts in its index
    // pages, and anything a page marks with the class "no-zoom".
    if (el.matches(".toggler, .no-zoom")) return null;
    var link = el.closest("a[href]");
    // An image that is a link to somewhere else keeps behaving as a link.
    // Sphinx wraps resized images in a link to the image file itself; that
    // link is replaced by the viewer.
    if (link && !link.classList.contains("image-reference")) return null;
    return el;
  }

  function describe(el) {
    if (el.tagName.toLowerCase() === "img") return el.getAttribute("alt") || "";
    var fig = el.closest("figure");
    var cap = fig && fig.querySelector("figcaption");
    return cap ? cap.textContent.trim() : "Flow chart";
  }

  function mark(root) {
    if (!(root instanceof Element) && root !== document) return;
    var found = root.querySelectorAll(IMG + ", " + CHART);
    for (var i = 0; i < found.length; i++) {
      var el = found[i];
      if (el.classList.contains("image-zoom-target") || !zoomTarget(el)) continue;
      el.classList.add("image-zoom-target");
      if (el.closest("a[href]")) continue; // the link is already focusable
      el.setAttribute("tabindex", "0");
      el.setAttribute("role", "button");
      var text = describe(el);
      el.setAttribute("aria-label", "Enlarge picture" + (text ? ": " + text : ""));
    }
  }

  /* ---- The viewer --------------------------------------------------- */

  function button(label, text, action) {
    var b = document.createElement("button");
    b.type = "button";
    b.textContent = text;
    b.setAttribute("aria-label", label);
    b.title = label;
    b.addEventListener("click", function (e) {
      e.stopPropagation();
      action();
    });
    return b;
  }

  function build() {
    overlay = document.createElement("div");
    overlay.className = "image-zoom-overlay";
    overlay.setAttribute("role", "dialog");
    overlay.setAttribute("aria-modal", "true");
    overlay.setAttribute("aria-label", "Enlarged picture");
    overlay.hidden = true;

    var bar = document.createElement("div");
    bar.className = "image-zoom-bar";
    level = document.createElement("span");
    level.className = "image-zoom-level";
    level.setAttribute("aria-live", "polite");
    bar.appendChild(button("Zoom out (-)", "−", function () { zoomBy(1 / 1.5); }));
    bar.appendChild(level);
    bar.appendChild(button("Zoom in (+)", "+", function () { zoomBy(1.5); }));
    bar.appendChild(button("Fit to window (0)", "Fit", fit));
    var close_ = button("Close (Esc)", "×", close);
    close_.className = "image-zoom-close";
    bar.appendChild(close_);

    stage = document.createElement("div");
    stage.className = "image-zoom-stage";

    caption = document.createElement("div");
    caption.className = "image-zoom-caption";

    overlay.appendChild(stage);
    overlay.appendChild(bar);
    overlay.appendChild(caption);
    document.body.appendChild(overlay);

    stage.addEventListener("wheel", onWheel, { passive: false });
    stage.addEventListener("pointerdown", onPointerDown);
    stage.addEventListener("pointermove", onPointerMove);
    stage.addEventListener("pointerup", onPointerUp);
    stage.addEventListener("pointercancel", onPointerUp);
    overlay.addEventListener("keydown", onKey);
    window.addEventListener("resize", function () {
      if (item) { measure(); fit(); }
    });
  }

  function naturalSize(el) {
    var w, h;
    if (el.tagName.toLowerCase() === "img") {
      w = el.naturalWidth;
      h = el.naturalHeight;
    } else {
      var vb = el.viewBox && el.viewBox.baseVal;
      if (vb && vb.width && vb.height) { w = vb.width; h = vb.height; }
    }
    if (!w || !h) {
      var r = el.getBoundingClientRect();
      w = r.width || 1;
      h = r.height || 1;
    }
    return { w: w, h: h };
  }

  function isVector(el) {
    if (el.tagName.toLowerCase() !== "img") return true;
    return /\.svg([?#]|$)/i.test(el.currentSrc || el.src || "");
  }

  function measure() {
    var n = naturalSize(opener);
    var s = Math.min(stage.clientWidth * 0.96 / n.w, stage.clientHeight * 0.96 / n.h);
    // Drawings stay sharp at any size. Photographs and other pixel images
    // are not blown up past twice their own size to fill the window.
    if (!isVector(opener)) s = Math.min(s, 2);
    base.w = n.w * s;
    base.h = n.h * s;
  }

  function apply() {
    var w = base.w * view.zoom, h = base.h * view.zoom;
    var sw = stage.clientWidth, sh = stage.clientHeight;
    // Keep the picture centred while it is smaller than the window, and keep
    // its edges from being dragged past the middle when it is larger.
    view.x = w <= sw ? (sw - w) / 2 : Math.min(sw / 2, Math.max(sw / 2 - w, view.x));
    view.y = h <= sh ? (sh - h) / 2 : Math.min(sh / 2, Math.max(sh / 2 - h, view.y));
    item.style.width = w + "px";
    item.style.height = h + "px";
    item.style.transform = "translate(" + view.x + "px," + view.y + "px)";
    level.textContent = Math.round(view.zoom * 100) + "%";
    stage.classList.toggle("image-zoom-zoomed", view.zoom > 1.001);
  }

  function fit() {
    view.zoom = 1;
    view.x = 0;
    view.y = 0;
    apply();
  }

  // Zoom to `zoom`, keeping the point (cx, cy) of the stage under the cursor.
  function zoomTo(zoom, cx, cy) {
    zoom = Math.min(MAX_ZOOM, Math.max(1, zoom));
    if (cx === undefined) { cx = stage.clientWidth / 2; cy = stage.clientHeight / 2; }
    var k = zoom / view.zoom;
    view.x = cx - (cx - view.x) * k;
    view.y = cy - (cy - view.y) * k;
    view.zoom = zoom;
    apply();
  }

  function zoomBy(factor, cx, cy) { zoomTo(view.zoom * factor, cx, cy); }

  function open(el) {
    if (!overlay) build();
    opener = el;
    if (el.tagName.toLowerCase() === "img") {
      item = document.createElement("img");
      item.src = el.currentSrc || el.src;
      item.alt = el.alt;
    } else {
      // A flow chart is drawn into the page by the browser, so it is copied.
      item = el.cloneNode(true);
      item.removeAttribute("tabindex");
      item.removeAttribute("role");
      item.removeAttribute("aria-label");
      item.removeAttribute("width");
      item.removeAttribute("height");
      item.style.maxWidth = "none";
    }
    item.classList.remove("image-zoom-target");
    item.classList.add("image-zoom-item");
    item.draggable = false;
    stage.textContent = "";
    stage.appendChild(item);
    caption.textContent = describe(el);
    caption.hidden = !caption.textContent;

    savedOverflow = document.documentElement.style.overflow;
    document.documentElement.style.overflow = "hidden";
    overlay.hidden = false;
    measure();
    fit();
    overlay.querySelector(".image-zoom-close").focus();
  }

  function close() {
    if (!item) return;
    overlay.hidden = true;
    stage.textContent = "";
    item = null;
    pointers.clear();
    gesture = null;
    document.documentElement.style.overflow = savedOverflow;
    var back = opener.closest("a[href]") || opener;
    opener = null;
    if (back.focus) back.focus({ preventScroll: true });
  }

  /* ---- Mouse, touch and keyboard inside the viewer ------------------ */

  function local(e) {
    var r = stage.getBoundingClientRect();
    return { x: e.clientX - r.left, y: e.clientY - r.top };
  }

  function onWheel(e) {
    e.preventDefault();
    var p = local(e);
    var delta = e.deltaY * (e.deltaMode === 1 ? 16 : 1);
    zoomBy(Math.exp(-delta * 0.002), p.x, p.y);
  }

  function startGesture() {
    var pts = Array.from(pointers.values());
    if (pts.length === 1) {
      gesture = { kind: "drag", x: pts[0].x, y: pts[0].y, vx: view.x, vy: view.y, moved: false,
                  onItem: gesture ? gesture.onItem : false };
    } else if (pts.length >= 2) {
      gesture = { kind: "pinch", moved: true,
                  dist: Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y) || 1,
                  zoom: view.zoom };
    } else {
      gesture = null;
    }
  }

  function onPointerDown(e) {
    if (e.button !== undefined && e.button !== 0) return;
    stage.setPointerCapture(e.pointerId);
    pointers.set(e.pointerId, local(e));
    var onItem = item.contains(e.target);
    var wasMoved = gesture && gesture.moved;
    startGesture();
    if (gesture && gesture.kind === "drag") {
      gesture.onItem = onItem;
      gesture.moved = !!wasMoved;
    }
    e.preventDefault();
  }

  function onPointerMove(e) {
    if (!pointers.has(e.pointerId) || !gesture) return;
    var p = local(e);
    pointers.set(e.pointerId, p);
    var pts = Array.from(pointers.values());
    if (gesture.kind === "drag") {
      var dx = p.x - gesture.x, dy = p.y - gesture.y;
      if (!gesture.moved && Math.hypot(dx, dy) < 5) return;
      gesture.moved = true;
      stage.classList.add("image-zoom-dragging");
      view.x = gesture.vx + dx;
      view.y = gesture.vy + dy;
      apply();
    } else if (pts.length >= 2) {
      var dist = Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y) || 1;
      zoomTo(gesture.zoom * dist / gesture.dist,
             (pts[0].x + pts[1].x) / 2, (pts[0].y + pts[1].y) / 2);
    }
  }

  function onPointerUp(e) {
    if (!pointers.has(e.pointerId)) return;
    var p = pointers.get(e.pointerId);
    pointers.delete(e.pointerId);
    stage.classList.remove("image-zoom-dragging");
    var g = gesture;
    if (pointers.size) {
      startGesture();
      if (gesture) gesture.moved = true; // lifting one finger of a pinch is not a click
      return;
    }
    gesture = null;
    if (!g || g.moved || e.type === "pointercancel") return;
    // A plain click: on the picture it switches between the whole picture
    // and a close-up of the clicked spot; beside the picture it closes.
    if (!g.onItem) close();
    else if (view.zoom > 1.001) fit();
    else zoomTo(CLICK_ZOOM, p.x, p.y);
  }

  function onKey(e) {
    var step = 80;
    switch (e.key) {
      case "Escape": close(); break;
      case "+": case "=": zoomBy(1.5); break;
      case "-": case "_": zoomBy(1 / 1.5); break;
      case "0": fit(); break;
      case "ArrowLeft": view.x += step; apply(); break;
      case "ArrowRight": view.x -= step; apply(); break;
      case "ArrowUp": view.y += step; apply(); break;
      case "ArrowDown": view.y -= step; apply(); break;
      case "Tab": {
        // Keep keyboard focus inside the viewer while it is open.
        var buttons = overlay.querySelectorAll("button");
        var first = buttons[0], last = buttons[buttons.length - 1];
        if (e.shiftKey && document.activeElement === first) last.focus();
        else if (!e.shiftKey && document.activeElement === last) first.focus();
        else return;
        break;
      }
      default: return;
    }
    e.preventDefault();
    e.stopPropagation();
  }

  /* ---- Opening from the page ---------------------------------------- */

  document.addEventListener("click", function (e) {
    if (e.defaultPrevented || e.button !== 0) return;
    if (e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return; // open in new tab etc.
    var el = zoomTarget(e.target);
    if (!el) return;
    e.preventDefault();
    open(el);
  });

  document.addEventListener("keydown", function (e) {
    if (e.key !== "Enter" && e.key !== " ") return;
    var el = e.target;
    if (!(el instanceof Element) || !el.classList.contains("image-zoom-target")) return;
    if (el.getAttribute("role") !== "button") return;
    e.preventDefault();
    open(el);
  });

  function start() {
    mark(document);
    // Flow charts are drawn after the page loads, so watch for them.
    var roots = document.querySelectorAll(CONTENT);
    if (!roots.length || !window.MutationObserver) return;
    var observer = new MutationObserver(function (changes) {
      for (var i = 0; i < changes.length; i++) {
        var target = changes[i].target;
        mark(target instanceof Element ? (target.parentElement || target) : document);
      }
    });
    for (var i = 0; i < roots.length; i++) {
      observer.observe(roots[i], { childList: true, subtree: true });
    }
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
