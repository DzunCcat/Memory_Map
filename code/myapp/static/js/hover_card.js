$(document).ready(function() {
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    const csrftoken = getCookie('csrftoken');

    // ホバーカードの表示
    $(document).on('mouseenter', '.username-link', function() {
        var $link = $(this);
        var username = $link.data('username');
        console.log('Username:', username); // デバッグ用ログ
        var $hoverCardContainer = $link.closest('.user-container').find('.hover-card-container');

        if ($hoverCardContainer.children().length === 0) {
            $.ajax({
                url: '/accounts/hover_card/' + username + '/',
                method: 'GET',
                success: function(data) {
                    $hoverCardContainer.html(data);
                    $hoverCardContainer.find('.hover-card').removeClass('d-none').addClass('show');
                },
                error: function(xhr, status, error) {
                    console.error('An error occurred:', error);
                }
            });
        } else {
            $hoverCardContainer.find('.hover-card').removeClass('d-none').addClass('show');
        }
    });

    // ホバーカードおよびリンクからマウスが離れた時
    $(document).on('mouseleave', '.user-container, .hover-card', function(e) {
        var $hoverCardContainer = $(this).closest('.user-container').find('.hover-card-container');
        if (!$(e.relatedTarget).closest('.hover-card').length) {
            $hoverCardContainer.find('.hover-card').removeClass('show').addClass('d-none');
        }
    });

    // フォローボタンのクリックイベント
    $(document).on('click', '.follow-btn', function(e) {
        e.preventDefault();
        var $btn = $(this);
        var username = $btn.data('username');
        var action = $btn.data('action');
        var url = action === 'follow' ? '/accounts/follow/' + username + '/' : '/accounts/unfollow/' + username + '/';

        $.ajax({
            url: url,
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken
            },
            data: {
                csrfmiddlewaretoken: csrftoken
            },
            success: function(response) {
                if (response.status === 'success') {
                    updateFollowButton($btn, response.is_following);
                    updateFollowerCount($btn, response.follower_count);
                }
            },
            error: function(xhr, status, error) {
                console.error('An error occurred:', error);
            }
        });
    });

    function updateFollowButton($btn, isFollowing) {
        if (isFollowing) {
            $btn.text('フォロー解除').removeClass('btn-primary').addClass('btn-secondary').data('action', 'unfollow');
        } else {
            $btn.text('フォローする').removeClass('btn-secondary').addClass('btn-primary').data('action', 'follow');
        }
    }

    function updateFollowerCount($btn, count) {
        $btn.closest('.hover-card').find('.follower-count').text(count);
    }
});
