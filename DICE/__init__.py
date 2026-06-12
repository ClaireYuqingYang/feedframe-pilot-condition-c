from otree.api import *
import pandas as pd
import numpy as np
import re
import os
import random
import httplib2
from itertools import cycle
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit




doc = """
Mimic social media feeds with DICE.
"""


class C(BaseConstants):
    NAME_IN_URL = 'DICE'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

    RULES_TEMPLATE = "DICE/T_Rules.html"
    PRIVACY_TEMPLATE = "DICE/T_Privacy.html"
    TWEET_TEMPLATE = "DICE/T_Tweet.html"
    ATTENTION_TEMPLATE = "DICE/T_Attention_Check.html"
    TOPICS_TEMPLATE = "DICE/T_Trending_Topics.html"
    BANNER_TEMPLATE = "DICE/T_Banner_Ads.html"

class Subsession(BaseSubsession):
    # feed_conditions = models.StringField(doc='indicates the feed condition a player is randomly assigned to')
    pass

class Group(BaseGroup):
    pass


class Player(BasePlayer):
    # ad_condition = models.StringField(doc='indicates the ad condition a player is randomly assigned to')
    feed_condition = models.StringField(doc='indicates the feed condition a player is randomly assigned to')
    sequence = models.StringField(doc='prints the sequence of tweets based on doc_id')

    # cta = models.BooleanField(doc='indicates whether CTA was clicked or not')
    scroll_sequence = models.LongStringField(doc='tracks the sequence of feed items a participant scrolled through.')
    viewport_data = models.LongStringField(doc='tracks the time feed items were visible in a participants viewport.')
    likes_data = models.LongStringField(doc='tracks likes.', blank=True)
    replies_data = models.LongStringField(doc='tracks replies.', blank=True)
    retweets_data = models.LongStringField(doc='tracks reposts/retweets.', blank=True)
    shares_data = models.LongStringField(doc='tracks shares.', blank=True)

    touch_capability = models.BooleanField(doc="indicates whether a participant uses a touch device to access survey.",
                                           blank=True)
    device_type = models.StringField(doc="indicates the participant's device type based on screen width.",
                                           blank=True)



# FUNCTIONS -----
def get_set_condition(player):
    return player.participant.vars.get('set_condition', '')


def creating_session(subsession):

    # read data (from seesion config)
    df = read_feed(subsession.session.config['data_path'])
    tweets = preprocessing(df)
    players = subsession.get_players()
    for player in players:
        player.participant.tweets = tweets
        player.feed_condition = subsession.session.config.get('condition_name', '')
        player.participant.vars['set_condition'] = ''

    # if the file contains any conditions, read them an assign groups to it
    condition = subsession.session.config['condition_col']
    if condition in tweets.columns:
        feed_conditions = tweets[condition].unique()
        # subsession.feed_conditions = str(feed_conditions)
        for player in players:
            player.feed_condition = random.choice(feed_conditions)

    set_col = subsession.session.config.get('set_col', 'set')
    if set_col in tweets.columns:
        set_conditions = [str(value) for value in tweets[set_col].dropna().unique()]
        set_assignments = [value for _, value in zip(players, cycle(set_conditions))]
        random.shuffle(set_assignments)
        for player, set_condition in zip(players, set_assignments):
            player.participant.vars['set_condition'] = set_condition

    # set banner ad conditions based on images in directory
    # all_files = os.listdir('twitter/static/img')
    # ad_conditions = []
    # for file_name in all_files:
    #     if file_name[0].isalpha() and file_name[1:].lower().endswith('.png') and file_name[1] == '_':
    #         letter = file_name[0].upper()
    #         if letter not in ad_conditions:
    #             ad_conditions.append(letter)
    # ad_conditions = list(set(ad_conditions))
    # for player in subsession.get_players():
    #     player.ad_condition = random.choice(ad_conditions)

    # PREPARE DATA:
    # subset data based on condition (if any)
    # I need to find a way to deal with '' or "", that is, escape them.
    for player in players:
        tweets = player.participant.tweets
        condition = player.session.config['condition_col']
        if condition in tweets.columns:
            tweets = tweets[tweets[condition] == str(player.feed_condition)]
        set_col = player.session.config.get('set_col', 'set')
        set_condition = get_set_condition(player)
        if set_col in tweets.columns and set_condition:
            tweets = tweets[tweets[set_col].astype(str) == str(set_condition)]

        # sort or shuffle data
        sort_by = player.session.config.get('sort_by', '')
        if player.session.config.get('shuffle_feed', False):
            tweets = tweets.sample(frac=1)
            tweets.reset_index(drop=True, inplace=True)
        elif sort_by in tweets.columns:
            tweets = tweets.sort_values(by=sort_by, ascending=True)
        else:
            tweets = tweets.sample(frac=1)
            # Reset the index after shuffling
            tweets.reset_index(drop=True, inplace=True)

        # subset first rows
        # tweets = tweets.head(player.session.config['subset'])

        # index
        tweets['index'] = range(1, len(tweets) + 1)
        tweets['row'] = range(1, len(tweets) + 1)

        # participant vars
        player.participant.tweets = tweets

        # sequence
        player.sequence = ', '.join(map(str, tweets['doc_id'].tolist()))




# make pictures (if any) visible
def extract_media_path(text):
    value = str(text).strip().strip("'\"").strip(',')
    if value == '' or value.lower() in ['nan', 'none']:
        return ''

    urls = re.findall(r'https?://[^\s,]+', value)
    if urls:
        return urls[0].strip("'\",")

    static_paths = re.findall(r'/static/[^\s,]+', value)
    if static_paths:
        return static_paths[0].strip("'\",")

    if re.match(r'^(img|images|headlines)/[^\s,]+\.(png|jpe?g|gif|webp|svg)$', value, re.IGNORECASE):
        return f'/static/{value}'

    if re.match(r'^[^\s,]+\.(png|jpe?g|gif|webp|svg)$', value, re.IGNORECASE):
        return f'/static/img/{value}'

    return value

# check urls
h = httplib2.Http()
def check_url_exists(url):
    try:
        resp = h.request(url, 'HEAD')
        return int(resp[0]['status']) < 400
    except Exception:
        return False

# function that reads data
def read_feed(path):
    if re.match(r'^https?://\S+', path):
        if 'github' in path:
            tweets = pd.read_csv(path, sep=';')
        elif 'drive.google.com' in path:
            file_id = path.split('/')[-2]
            download_url = f'https://drive.google.com/uc?id={file_id}'
            tweets = pd.read_csv(download_url, sep=';')
        else:
            raise ValueError("Unrecognized URL format")
    else:
        tweets = pd.read_csv(path, sep=';')
    return tweets

# some pre-processing
def preprocessing(df):
    # reformat date
    df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
    df['date'] = df['datetime'].dt.strftime('%d %b').str.replace(' ', '. ')
    # df['date'] = df['datetime'].dt.strftime('%b. %d')
    df['date'] = df['date'].str.replace('^0', '', regex=True)

    # highlight hashtags, cashtags, mentions, etc.
    df['tweet'] = df['tweet'].str.replace(r'\B(\#[a-zA-Z0-9_]+\b)',
                                                  r'<span class="text-primary">\g<0></span>', regex=True)
    df['tweet'] = df['tweet'].str.replace(r'\B(\$[a-zA-Z0-9_\.]+\b)',
                                                  r'<span class="text-primary">\g<0></span>', regex=True)
    df['tweet'] = df['tweet'].str.replace(r'\B(\@[a-zA-Z0-9_]+\b)',
                                                  r'<span class="text-primary">\g<0></span>', regex=True)
    # remove the href below, if you don't want them to leave your page
    df['tweet'] = df['tweet'].str.replace(
        r'(http|ftp|https):\/\/([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])',
        r'<a class="text-primary">\g<0></a>', regex=True)

    # make numeric information integers and fill NAs with 0
    df['replies'] = df['replies'].fillna(0).astype(int)
    df['retweets'] = df['retweets'].fillna(0).astype(int)
    df['likes'] = df['likes'].fillna(0).astype(int)

    df['media'] = df['media'].apply(extract_media_path)
    df['media'] = df['media'].str.replace("'|,", '', regex=True)
    df['pic_available'] = np.where(df['media'].fillna('').str.match(pat=r'^(https?://|/static/)'), True, False)

    # create a name icon as a profile pic
    df['icon'] = df['username'].str[:2]
    df['icon'] = df['icon'].str.title()

    # make sure user descriptions do not entail any '' or "" as this complicates visualization
    # also replace nan with some whitespace
    df['user_description'] = df['user_description'].str.replace("'", '')
    df['user_description'] = df['user_description'].str.replace('"', '')
    df['user_description'] = df['user_description'].fillna(' ')

    # make number of followers a formatted string
    df['user_followers'] = df['user_followers'].map('{:,.0f}'.format).str.replace(',', '.')

    # check profile image urls
    # df['profile_pic_available'] = df['user_image'].apply(
        # lambda x: check_url_exists(x) if pd.notnull(x) else False)
    df['profile_pic_available'] = True

    return df


def create_redirect(player):
    split_link = urlsplit(player.session.config['survey_link'])
    query_params = dict(parse_qsl(split_link.query))
    query_params[player.session.config['url_param']] = player.participant.label or player.participant.code
    query_params['condition'] = player.session.config.get('condition_name', '')
    query_params['set_condition'] = get_set_condition(player)

    completion_code = None

    # if 'prolific_completion_url' in player.session.config and player.session.config['prolific_completion_url'] is not None:
        # completion_code = player.session.config['prolific_completion_url'][-8:]

    if 'completion_code' in player.session.vars:
        if player.session.vars['completion_code'] is not None:
            query_params['cc'] = player.session.vars['completion_code']

    return urlunsplit(split_link._replace(query=urlencode(query_params)))


# PAGES
class A_Intro(Page):
    form_model = 'player'
    @staticmethod
    def before_next_page(player, timeout_happened):
        pass

class B_Briefing(Page):
    form_model = 'player'

    @staticmethod
    def is_displayed(player):
        return len(player.session.config['briefing']) > 0


class C_Feed(Page):
    form_model = 'player'

    @staticmethod
    def get_form_fields(player: Player):
        fields =  ['likes_data', 'replies_data', 'retweets_data', 'shares_data', 'touch_capability', 'device_type']

        if not player.session.config['topics'] & player.session.config['show_cta']:
            more_fields =  ['scroll_sequence', 'viewport_data'] # , 'cta']
        else:
            more_fields =  ['scroll_sequence', 'viewport_data']

        return fields + more_fields

    @staticmethod
    def vars_for_template(player: Player):
        # ad = player.ad_condition
        label_available = False
        if player.participant.label is not None:
            label_available = True
        return dict(
            tweets=player.participant.tweets.to_dict('index'),
            topics=player.session.config['topics'],
            search_term=player.session.config['search_term'],
            label_available=label_available,
            # banner_img='img/{}_banner.png'.format(ad),
        )

    @staticmethod
    def live_method(player, data):
        parts = data.split('=')
        variable_name = parts[0].strip()
        value = eval(parts[1].strip())

        # Use getattr to get the current value of the attribute within the player object
        current_value = getattr(player, variable_name, 0)

        # Perform the addition assignment and update the attribute within the player object
        setattr(player, variable_name, current_value + value)

    @staticmethod
    def before_next_page(player, timeout_happened):
        player.participant.finished = True
        if 'prolific_completion_url' in player.session.vars:
            if player.session.vars['prolific_completion_url'] is not None:
                if 'completion_code' in player.session.vars:
                    if player.session.vars['completion_code'] is not None:
                        player.session.vars['prolific_completion_url'] = 'https://app.prolific.com/submissions/complete?cc=' + player.session.vars['completion_code']
                    else:
                        player.session.vars['prolific_completion_url'] = 'https://app.prolific.com/submissions/complete'
                else: player.session.vars['prolific_completion_url'] = 'https://app.prolific.com/submissions/complete'
            else:
                player.session.vars['prolific_completion_url'] = 'NA'
        else:
            player.session.vars['prolific_completion_url'] = 'NA'

class D_Redirect(Page):

    @staticmethod
    def is_displayed(player):
        return len(player.session.config['survey_link']) > 0

    @staticmethod
    def vars_for_template(player: Player):
        return dict(link=create_redirect(player))

    @staticmethod
    def js_vars(player):
        return dict(link=create_redirect(player))

class D_Debrief(Page):

    @staticmethod
    def is_displayed(player):
        return len(player.session.config['survey_link']) == 0

page_sequence = [A_Intro,
                 B_Briefing,
                 C_Feed,
                 D_Redirect,
                 D_Debrief]


def custom_export(players):
    # header row
    yield ['session', 'participant_code', 'participant_label', 'participant_in_session', 'condition', 'set_condition', 'item_sequence',
           'scroll_sequence', 'item_dwell_time', 'likes', 'replies', 'retweets', 'shares']
    for p in players:
        participant = p.participant
        session = p.session
        yield [session.code, participant.code, participant.label, p.id_in_group, p.feed_condition, get_set_condition(p), p.sequence,
               p.scroll_sequence, p.viewport_data, p.likes_data, p.replies_data, p.retweets_data, p.shares_data]
