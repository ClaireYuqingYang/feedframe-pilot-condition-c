console.log("Reactions ready!");

document.addEventListener('DOMContentLoaded', function() {
    let repliesData = [];
    let likesData = [];
    let retweetsData = [];
    let sharesData = [];

    function withMode(record, mode) {
        if (typeof window.currentFeedMode !== "undefined") {
            record.mode = mode || window.currentFeedMode || "default";
        }
        return record;
    }

    // Function to toggle the like state of a button
    function toggleLike(button) {
        const icon = button.querySelector('.like-icon');
        const likeCountSpan = button.querySelector('.like-count');
        let likeCount = parseInt(likeCountSpan.textContent);

        if (icon.classList.contains('bi-heart')) {
            icon.classList.remove('bi-heart', 'text-secondary');
            icon.classList.add('bi-heart-fill', 'text-danger');
            likeCount++;
        } else {
            icon.classList.remove('bi-heart-fill', 'text-danger');
            icon.classList.add('bi-heart', 'text-secondary');
            likeCount--;
        }

        likeCountSpan.textContent = likeCount.toString();
    }

    // Attach event listeners to all like buttons
    document.querySelectorAll('.like-button').forEach(button => {
        button.addEventListener('click', function() {
            toggleLike(button);
        });
    });

    document.querySelectorAll('.retweet-button').forEach(button => {
        button.addEventListener('click', function() {
            button.dataset.retweetMode = window.currentFeedMode || "default";
        });
    });

    document.querySelectorAll('.share-button').forEach(button => {
        button.addEventListener('click', function() {
            button.dataset.shareMode = window.currentFeedMode || "default";
        });
    });

    // Function to handle reply submission and class change
    function replyOneUp(docId) {
        const replyField = document.getElementById(`reply_to_item_${docId}`);
        const replyText = replyField.value.trim();
        const replyCountSpan = document.getElementById(`reply_count_${docId}`);
        const replyIcon = document.getElementById(`reply_icon_${docId}`);

        if (replyText) {
            replyIcon.classList.remove('bi-chat', 'text-secondary');
            replyIcon.classList.add('bi-chat-fill', 'text-primary');

            let replyCount = parseInt(replyCountSpan.textContent);
            replyCount++;
            replyCountSpan.textContent = replyCount.toString();

            replyField.value = '';
            repliesData.push({ doc_id: docId, reply: replyText });
        }
    }

    // Attach event listeners to reply modal buttons
    document.querySelectorAll('.reply-modal-button').forEach(button => {
        button.addEventListener('click', function() {
            const docId = this.id.replace('reply_modal_button_', '');
            replyOneUp(docId);
        });
    });

    // Function to collect likes
    function collectLikes() {
        document.querySelectorAll('.like-button').forEach(button => {
            let docId = button.getAttribute('id').replace('like_button_', '');
            let icon = button.querySelector('.like-icon');
            let isLiked = icon.classList.contains('bi-heart-fill');
            likesData.push({ doc_id: docId, liked: isLiked });
        });
    }

    function collectRetweets() {
        document.querySelectorAll('.retweet-button').forEach(button => {
            let docId = button.getAttribute('id').replace('retweet_button_', '');
            let isRetweeted = button.classList.contains('retweeted');
            let mode = button.dataset.retweetMode || window.currentFeedMode || "default";
            retweetsData.push(withMode({ doc_id: docId, retweeted: isRetweeted }, mode));
        });
    }

    function collectShares() {
        document.querySelectorAll('.share-button').forEach(button => {
            let docId = button.getAttribute('id').replace('share_button_', '');
            let isShared = button.classList.contains('shared');
            let mode = button.dataset.shareMode || window.currentFeedMode || "default";
            sharesData.push(withMode({ doc_id: docId, shared: isShared }, mode));
        });
    }

    // Function to collect data
    function collectData() {
        collectLikes();  // Populates the likesData array
        collectRetweets();
        collectShares();
        return {
            likes: JSON.stringify(likesData),
            replies: JSON.stringify(repliesData),
            retweets: JSON.stringify(retweetsData),
            shares: JSON.stringify(sharesData)
        };
    }

    // Event listener for the submit button
    document.getElementById('submitButton').addEventListener('click', function(event) {
        //event.preventDefault();
        let data = collectData();
        document.getElementById('likes_data').value = data.likes;
        document.getElementById('replies_data').value = data.replies;
        document.getElementById('retweets_data').value = data.retweets;
        document.getElementById('shares_data').value = data.shares;
        console.log("Data to send:", data);
    });

    // Function to display tweet content in the modal
    function displayTweetContent(docId, tweetContent) {
        const replyingTweetDiv = document.getElementById(`replying_tweet_${docId}`);
        replyingTweetDiv.textContent = tweetContent;
    }

    // Attach event listeners to open modal and display tweet content
    document.querySelectorAll('.reply-button').forEach(button => {
        button.addEventListener('click', function() {
            const docId = this.id.replace('reply_button_', '');
            let yourTweetContent = document.getElementById("tweet_text_" + docId).textContent;
            displayTweetContent(docId, yourTweetContent);
        });
    });
});
