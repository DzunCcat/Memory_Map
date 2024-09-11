Dropzone.autoDiscover = false;

function initializeAllDropzones() {
  var dropzones = document.querySelectorAll(".dropzone:not(.dz-initialized)");
  dropzones.forEach(function (dropzoneElement) {
    var formId = dropzoneElement.id.replace("comment-dropzone-", "");
    initializeDropzone(formId);
  });
}

function initializeDropzone(formId) {
  console.log("Initializing Dropzone for", formId);
  var dropzoneElement = document.getElementById("comment-dropzone-" + formId);
  if (dropzoneElement && !dropzoneElement.dropzone) {
    console.log("Dropzone element found, creating instance");
    var dz = new Dropzone("#comment-dropzone-" + formId, {
      url: dropzoneElement.dataset.url,
      maxFilesize: dropzoneElement.dataset.maxFilesize,
      acceptedFiles: dropzoneElement.dataset.acceptedFiles,
      addRemoveLinks: true,
      autoProcessQueue: false,
      uploadMultiple: false,
      parallelUploads: 5,
      maxFiles: 5,
      paramName: "file",
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
      },
      init: function () {
        var dzInstance = this;
        document
          .getElementById("comment-form-" + formId)
          .addEventListener("submit", function (e) {
            e.preventDefault();
            if (dzInstance.getQueuedFiles().length > 0) {
              dzInstance.processQueue();
            } else {
              submitForm(formId);
            }
          });

        dzInstance.on("sending", function (file, xhr, formData) {
          var form = document.getElementById("comment-form-" + formId);
          var formDataEntries = new FormData(form);
          for (var pair of formDataEntries.entries()) {
            if (pair[0] !== "file") {
              formData.append(pair[0], pair[1]);
            }
          }
        });

        dzInstance.on("success", function (file, response) {
          var fileIds = document.getElementById("file_ids-" + formId);
          if (fileIds.value) {
            fileIds.value += "," + response.file_id;
          } else {
            fileIds.value = response.file_id;
          }
        });

        dzInstance.on("queuecomplete", function () {
          submitForm(formId);
        });

        dzInstance.on("error", function (file, errorMessage) {
          console.error("Upload error:", errorMessage);
          alert(
            "ファイルのアップロードに失敗しました: " +
              JSON.stringify(errorMessage)
          );
        });
      },
    });

    dropzoneElement.dropzone = dz;
    dropzoneElement.classList.add("dz-initialized");

    console.log("Dropzone initialized for", formId);
  } else {
    console.log("Dropzone element not found or already initialized");
  }
}

function submitForm(formId) {
  var form = document.getElementById("comment-form-" + formId);
  var formData = new FormData(form);
  fetch(form.action, {
    method: "POST",
    body: formData,
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "success") {
        reloadComments();
        form.reset();
        var dropzone = Dropzone.forElement("#comment-dropzone-" + formId);
        if (dropzone) {
          dropzone.removeAllFiles();
        }
        if (formId !== "main") {
          form.style.display = "none";
        }
      } else {
        alert("エラーが発生しました。もう一度お試しください。");
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      alert("エラーが発生しました。もう一度お試しください。");
    });
}

function submitEditForm(commentId) {
  var form = document.getElementById(`edit-form-${commentId}`);
  var formData = new FormData(form);
  formData.append("csrfmiddlewaretoken", getCookie("csrftoken"));
  formData.append("content_type", "tweet"); // または適切な値
  formData.append("visibility", "public"); // または適切な値

  // デバッグ用：送信するデータの内容をログ出力
  for (var pair of formData.entries()) {
    console.log(pair[0] + ": " + pair[1]);
  }

  fetch(`/memorymap/comment/${commentId}/edit/`, {
    method: "POST",
    body: formData,
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "success") {
        reloadComments();
      } else {
        console.error("Edit error:", data.errors);
        alert(
          "コメントの更新に失敗しました。エラー: " + JSON.stringify(data.errors)
        );
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      alert("エラーが発生しました。もう一度お試しください。");
    });
}

function toggleReplyForm(commentId) {
  var form = document.getElementById("comment-form-" + commentId);
  if (form.style.display === "none" || form.style.display === "") {
    form.style.display = "block";
    var dropzoneElement = document.getElementById(
      "comment-dropzone-" + commentId
    );
    if (dropzoneElement && !dropzoneElement.dropzone) {
      initializeDropzone(commentId);
    }
  } else {
    form.style.display = "none";
  }
}

function editComment(commentId) {
  var commentElement = document.getElementById("comment-" + commentId);
  var contentElement = commentElement.querySelector(".comment-content");
  var currentContent = contentElement.innerHTML.trim();

  var existingForm = commentElement.querySelector(".edit-comment-form");
  if (existingForm) {
    existingForm.remove();
  }

  var formHtml = `
    <form id="edit-form-${commentId}" class="edit-comment-form">
      <textarea name="content" class="form-control">${currentContent}</textarea>
      <button type="submit" class="btn btn-primary mt-2">更新</button>
      <button type="button" class="btn btn-secondary mt-2" onclick="cancelEdit(${commentId})">キャンセル</button>
    </form>
  `;

  contentElement.style.display = "none";
  contentElement.insertAdjacentHTML("afterend", formHtml);

  document
    .getElementById(`edit-form-${commentId}`)
    .addEventListener("submit", function (e) {
      e.preventDefault();
      submitEditForm(commentId);
    });
}

function setupCommentEventListeners(commentElement) {
  var replyButton = commentElement.querySelector(".btn-outline-primary");
  var editButton = commentElement.querySelector(".btn-outline-secondary");
  var deleteButton = commentElement.querySelector(".btn-outline-danger");
  var commentId = commentElement.id.split("-")[1];

  if (replyButton && !replyButton.hasEventListener) {
    replyButton.addEventListener("click", function () {
      toggleReplyForm(commentId);
    });
    replyButton.hasEventListener = true;
  }

  if (editButton && !editButton.hasEventListener) {
    editButton.addEventListener("click", function () {
      editComment(commentId);
    });
    editButton.hasEventListener = true;
  }

  if (deleteButton && !deleteButton.hasEventListener) {
    deleteButton.addEventListener("click", function () {
      deleteComment(commentId);
    });
    deleteButton.hasEventListener = true;
  }
}

function cancelEdit(commentId) {
  var commentElement = document.getElementById("comment-" + commentId);
  var contentElement = commentElement.querySelector(".comment-content");
  var editForm = commentElement.querySelector(".edit-comment-form");

  if (editForm) {
    editForm.remove();
  }
  contentElement.style.display = "";
}

function deleteComment(commentId) {
  if (confirm("本当にこのコメントを削除しますか？")) {
    const commentElement = document.getElementById(`comment-${commentId}`);
    if (commentElement) {
      commentElement.style.opacity = "0.5"; // 削除中の視覚的フィードバック
    }
    fetch(`/memorymap/comment/${commentId}/delete/`, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
      },
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.status === "success") {
          // ページ全体を再読み込みする代わりに、該当のコメント要素のみを削除
          const commentElement = document.getElementById(
            `comment-${commentId}`
          );
          if (commentElement) {
            commentElement.remove();
          }
        } else {
          if (commentElement) {
            commentElement.style.opacity = "1"; // 削除失敗時に元に戻す
          }
          alert("コメントの削除に失敗しました。");
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        alert("エラーが発生しました。もう一度お試しください。");
      });
  }
}

function restructureComments() {
  var comments = document.querySelectorAll(".comment");
  comments.forEach(function (comment) {
    var parentId = comment.dataset.parentId;
    if (parentId && parentId !== "main") {
      var parentComment = document.getElementById("comment-" + parentId);
      if (parentComment) {
        var childrenContainer = parentComment.querySelector(".children");
        if (!childrenContainer) {
          childrenContainer = document.createElement("div");
          childrenContainer.className = "children ml-4";
          parentComment.appendChild(childrenContainer);
        }
        childrenContainer.appendChild(comment);
      }
    }
  });
}

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function reloadComments() {
  fetch(window.postDetailUrl)
    .then((response) => response.text())
    .then((html) => {
      var newCommentsContainer = document.createElement("div");
      newCommentsContainer.innerHTML = html;
      var updatedCommentsContainer = newCommentsContainer.querySelector(
        "#comments-container"
      );
      if (updatedCommentsContainer) {
        document.getElementById("comments-container").innerHTML =
          updatedCommentsContainer.innerHTML;
        var comments = document.querySelectorAll(".comment");
        comments.forEach(setupCommentEventListeners);
        restructureComments();
        // initializeAllDropzones(); を削除
      } else {
        console.error("Could not find comments container in the response");
      }
    })
    .catch((error) => {
      console.error("Error reloading comments:", error);
    });
}

document.addEventListener("DOMContentLoaded", function () {
  console.log("DOM fully loaded");
  initializeDropzone("main"); // メインのコメントフォームのみ初期化
  restructureComments();
  var comments = document.querySelectorAll(".comment");
  comments.forEach(setupCommentEventListeners);
});
