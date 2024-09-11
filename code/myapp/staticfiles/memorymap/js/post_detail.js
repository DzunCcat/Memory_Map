function initializePostDetail(config) {
    Dropzone.autoDiscover = false;
  
    const commentsContainer = document.getElementById('comments-container');
  
    function initializeDropzone(formId) {
      console.log('Initializing Dropzone for', formId);
      const dropzoneElement = document.getElementById('comment-dropzone-' + formId);
      if (dropzoneElement && !dropzoneElement.dropzone) {
        console.log('Dropzone element found, creating instance');
        new Dropzone("#comment-dropzone-" + formId, {
          url: config.urls.fileUpload,
          maxFilesize: config.dropzoneConfig.maxFilesize,
          acceptedFiles: config.dropzoneConfig.acceptedFiles,
          addRemoveLinks: true,
          autoProcessQueue: false,
          uploadMultiple: false,
          parallelUploads: 5,
          maxFiles: 5,
          paramName: "file",
          headers: {
            'X-CSRFToken': config.csrfToken
          },
          init: function() {
            var dz = this;
            document.getElementById("comment-form-" + formId).addEventListener("submit", function(e) {
              e.preventDefault();
              if (dz.getQueuedFiles().length > 0) {
                dz.processQueue();
              } else {
                submitForm(formId);
              }
            });
  
            dz.on("sending", function(file, xhr, formData) {
              var form = document.getElementById("comment-form-" + formId);
              var formDataEntries = new FormData(form);
              for (var pair of formDataEntries.entries()) {
                if (pair[0] !== 'file') {
                  formData.append(pair[0], pair[1]);
                }
              }
            });
  
            dz.on("success", function(file, response) {
              var fileIds = document.getElementById("file_ids-" + formId);
              if (fileIds.value) {
                fileIds.value += ',' + response.file_id;
              } else {
                fileIds.value = response.file_id;
              }
            });
  
            dz.on("queuecomplete", function() {
              submitForm(formId);
            });
  
            dz.on("error", function(file, errorMessage) {
              console.error("Upload error:", errorMessage);
              alert("ファイルのアップロードに失敗しました: " + JSON.stringify(errorMessage));
            });
          }
        });
      } else {
        console.log('Dropzone element not found or already initialized');
      }
    }
  
    async function submitForm(formId) {
      const form = document.getElementById("comment-form-" + formId);
      const formData = new FormData(form);
  
      try {
        const response = await fetch(config.urls.addComment, {
          method: "POST",
          body: formData,
          headers: {
            'X-CSRFToken': config.csrfToken
          }
        });
  
        const data = await response.json();
  
        if (data.status === 'success') {
          const newCommentHtml = data.html;
          if (formId === 'main') {
            commentsContainer.insertAdjacentHTML('beforeend', newCommentHtml);
          } else {
            const parentComment = document.getElementById("comment-" + formId);
            let childCommentsContainer = parentComment.querySelector('.children');
            if (!childCommentsContainer) {
              childCommentsContainer = document.createElement('div');
              childCommentsContainer.className = 'children ml-4';
              parentComment.appendChild(childCommentsContainer);
            }
            childCommentsContainer.insertAdjacentHTML('beforeend', newCommentHtml);
          }
          const newComment = document.getElementById("comment-" + data.comment_id);
          if (newComment) {
            setupCommentEventListeners(newComment);
          }
          form.reset();
          Dropzone.forElement("#comment-dropzone-" + formId).removeAllFiles();
          if (formId !== 'main') {
            form.style.display = 'none';
          }
        } else {
          throw new Error('サーバーエラー');
        }
      } catch (error) {
        console.error('Error:', error);
        alert('エラーが発生しました。もう一度お試しください。');
      }
    }
  
    function toggleReplyForm(commentId) {
      const form = document.getElementById("comment-form-" + commentId);
      if (form) {
        if (form.style.display === 'none' || form.style.display === '') {
          form.style.display = 'block';
          initializeDropzone(commentId);
        } else {
          form.style.display = 'none';
        }
      } else {
        console.error('Reply form not found for comment ID:', commentId);
      }
    }
  
    function editComment(commentId) {
      const commentElement = document.getElementById("comment-" + commentId);
      const contentElement = commentElement.querySelector(".comment-content");
      const currentContent = contentElement.getAttribute("data-original-content");
      
      // 既存の編集フォームがあれば削除
      const existingForm = commentElement.querySelector('.edit-comment-form');
      if (existingForm) {
        existingForm.remove();
      }
  
      const formHtml = `
        <form id="edit-form-${commentId}" class="edit-comment-form">
          <textarea name="content" class="form-control">${currentContent}</textarea>
          <button type="submit" class="btn btn-primary mt-2">更新</button>
          <button type="button" class="btn btn-secondary mt-2" onclick="cancelEdit(${commentId})">キャンセル</button>
        </form>
      `;
      
      // 元のコンテンツを非表示にし、フォームを挿入
      contentElement.style.display = 'none';
      contentElement.insertAdjacentHTML('afterend', formHtml);
      
      document.getElementById(`edit-form-${commentId}`).addEventListener('submit', function(e) {
        e.preventDefault();
        submitEditForm(commentId);
      });
    }
  
    async function submitEditForm(commentId) {
      const form = document.getElementById(`edit-form-${commentId}`);
      const formData = new FormData(form);
      formData.append('csrfmiddlewaretoken', config.csrfToken);
      formData.append('content_type', 'tweet');
      formData.append('visibility', 'public');
  
      try {
        const response = await fetch(config.urls.editComment.replace('0', commentId), {
          method: "POST",
          body: formData,
          headers: {
            'X-CSRFToken': config.csrfToken
          }
        });
  
        const data = await response.json();
  
        if (data.status === 'success') {
          const commentElement = document.getElementById("comment-" + commentId);
          commentElement.outerHTML = data.html;
          
          const newCommentElement = document.getElementById("comment-" + commentId);
          setupCommentEventListeners(newCommentElement);
        } else {
          throw new Error('編集エラー');
        }
      } catch (error) {
        console.error('Error:', error);
        alert('コメントの更新に失敗しました。');
      }
    }
  
    function cancelEdit(commentId) {
      const commentElement = document.getElementById("comment-" + commentId);
      const contentElement = commentElement.querySelector(".comment-content");
      const editForm = commentElement.querySelector('.edit-comment-form');
  
      if (editForm) {
        editForm.remove();
      }
      contentElement.style.display = ''; // 元のコンテンツを再表示
    }
  
    async function deleteComment(commentId) {
      if (confirm('本当にこのコメントを削除しますか？')) {
        try {
          const response = await fetch(config.urls.deleteComment.replace('0', commentId), {
            method: "POST",
            headers: {
              'X-CSRFToken': config.csrfToken
            }
          });
  
          const data = await response.json();
  
          if (data.status === 'success') {
            const commentElement = document.getElementById("comment-" + commentId);
            commentElement.remove();
          } else {
            throw new Error('削除エラー');
          }
        } catch (error) {
          console.error('Error:', error);
          alert('コメントの削除に失敗しました。');
        }
      }
    }
  
    function setupCommentEventListeners(commentElement) {
      const replyButton = commentElement.querySelector('.btn-outline-primary');
      const editButton = commentElement.querySelector('.btn-outline-secondary');
      const deleteButton = commentElement.querySelector('.btn-outline-danger');
  
      if (replyButton) {
        replyButton.addEventListener('click', function() {
          const commentId = this.closest('.comment').id.split('-')[1];
          toggleReplyForm(commentId);
        });
      }
  
      if (editButton) {
        editButton.addEventListener('click', function() {
          const commentId = this.closest('.comment').id.split('-')[1];
          editComment(commentId);
        });
      }
  
      if (deleteButton) {
        deleteButton.addEventListener('click', function() {
          const commentId = this.closest('.comment').id.split('-')[1];
          deleteComment(commentId);
        });
      }
    }
  
    function restructureComments() {
      const comments = document.querySelectorAll('.comment');
      comments.forEach(function(comment) {
        const parentId = comment.dataset.parentId;
        if (parentId && parentId !== 'main') {
          const parentComment = document.getElementById('comment-' + parentId);
          if (parentComment) {
            let childrenContainer = parentComment.querySelector('.children');
            if (!childrenContainer) {
              childrenContainer = document.createElement('div');
              childrenContainer.className = 'children ml-4';
              parentComment.appendChild(childrenContainer);
            }
            childrenContainer.appendChild(comment);
          }
        }
      });
    }
  
    // 初期化
    initializeDropzone('main');
    restructureComments();
    const comments = document.querySelectorAll('.comment');
    comments.forEach(setupCommentEventListeners);
  
    // イベントデリゲーション
    commentsContainer.addEventListener('click', function(e) {
      if (e.target.classList.contains('btn-outline-primary')) {
        const commentId = e.target.closest('.comment').id.split('-')[1];
        toggleReplyForm(commentId);
      } else if (e.target.classList.contains('btn-outline-secondary')) {
        const commentId = e.target.closest('.comment').id.split('-')[1];
        editComment(commentId);
      } else if (e.target.classList.contains('btn-outline-danger')) {
        const commentId = e.target.closest('.comment').id.split('-')[1];
        deleteComment(commentId);
      }
    });
  }