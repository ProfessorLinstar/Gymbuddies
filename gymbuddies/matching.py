"""Matching page blueprint. Provides routes for
  1. Finding matches
  2. Pending matches
  3. Matches
"""

from datetime import datetime, timezone

from typing import Dict, Any, List
from flask import Blueprint
from flask import render_template, redirect, url_for
from flask import session, g, request
from .error import NoLoginError
from . import common, error
from . import database
from . import sendsms
from .database import db

bp = Blueprint("matching", __name__, url_prefix="/matching")


@bp.route("/findabuddy", methods=("GET", "POST"))
@error.guard_decorator()
def findabuddy():
    # get the current user in the session
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("home.index"))
    if not database.user.user_profile_valid(netid):
        return redirect(url_for("home.newuser"))

    if request.method == "POST":
        destnetid = request.form["destnetid"]
        schedule = common.json_to_schedule(request.form["jsoncalendar"])

        session["index"] += 1
        database.request.new(netid, destnetid, schedule)
        # ADD SMS MESSAGING HERE
        if sendsms.SEND_SMS:
            if database.user.get_notification_status(destnetid):
                username = database.user.get_name(netid)
                number = database.user.get_contact(destnetid)
                success = sendsms.sendsms("1" + number,
                                          sendsms.NEW_REQUEST_MESSAGE.replace("$netid$", netid).replace("$username$", username))
                print("sent to this number:", number)
                print(success)
        # return redirect(url_for("matching.outgoing"))
        print("inside findabuddy POST")
        return ""

    # implement the roundtable format of getting matches
    sess_index = request.args.get("index")
    if sess_index is not None:
        sess_index = int(sess_index)
        session["index"] += 1

    # get the users and index of current user that you have been matched with
    matches: List[str] = session.get("matches", None)
    index: int = session.get("index", None)
    if not matches or index >= len(matches):
        session["matches"] = database.matchmaker.find_matches(netid)
        session["index"] = 0
        matches = session.get("matches", None)
        index = session.get("index", None)
        no_matches = True
        return render_template("findabuddy.html", netid=netid, no_matches=no_matches)

    no_matches = False

    # TODO: handle if g.user is None (e.g. if user is deleted but matches are preserved)
    # TODO: when no more matches -- index out of bound error
    # generate "no more matches message"
    if len(matches) == 0:
        no_matches = True
        return render_template("findabuddy.html", netid=netid, no_matches=no_matches)

    g.user = database.user.get_user(
        matches[index])  # can access this in jinja template with {{ g.user }}
    # g.requests = database.request.get_active_incoming(netid)
    level = database.db.Level(g.user.level)
    level = level.to_readable()
    interests = database.user.get_interests_string(netid)
    # grab schedule
    context: Dict[str, Any] = {}

    common.fill_schedule(context, g.user.schedule)

    return render_template("findabuddy.html",
                           no_matches=no_matches,
                           netid=netid,
                           level=level,
                           interests=interests,
                           user=g.user,
                           **context)


@bp.route("/buddies", methods=["GET"])
@error.guard_decorator()
def buddies():
    """get the current user in the session"""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("home.index"))

    # implement the roundtable format of getting matches
    sess_index = request.args.get("index")
    if sess_index is not None:
        sess_index = int(sess_index)
        session["index"] += 1

    # get the users and index of current user that you have been matched with
    matches: List[str] = session.get("matches", None)
    index: int = session.get("index", None)
    if not matches or index >= len(matches):
        session["matches"] = database.matchmaker.find_matches(netid)
        session["index"] = 0
        matches = session.get("matches", None)
        index = session.get("index", None)
        no_matches = True
        return render_template("buddies.html", netid=netid, no_matches=no_matches, end_of_index=True)

    no_matches = False

    if len(matches) == 0:
        no_matches = True
        return render_template("findabuddy.html", netid=netid, no_matches=no_matches)

    g.user = database.user.get_user(
        matches[index])  # can access this in jinja template with {{ g.user }}
    # g.requests = database.request.get_active_incoming(netid)
    level = database.db.Level(g.user.level)
    level = level.to_readable()
    interests = database.user.get_interests_string(netid)

    destuserSchedule = g.user.schedule
    srcuser = database.user.get_user(netid)
    srcuserSchedule = srcuser.schedule
    # will hold combination of request and user schedule
    combinedSchedule: List[int] = [db.ScheduleStatus.UNAVAILABLE] * db.NUM_WEEK_BLOCKS
    for i in range(len(combinedSchedule)):
        if srcuserSchedule[i] == destuserSchedule[i] == db.ScheduleStatus.AVAILABLE:
            combinedSchedule[i] = db.ScheduleStatus.AVAILABLE

    # grab schedule
    context: Dict[str, Any] = {}
    common.fill_schedule(context, combinedSchedule)

    return render_template("buddies.html",
                           no_matches=no_matches,
                           end_of_index=False,
                           netid=netid,
                           level=level,
                           interests=interests,
                           user=g.user,
                           **context)


@bp.route("/incoming", methods=("GET",))
@error.guard_decorator()
def incoming():
    """Page for incoming requests."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("home.index"))
    if not database.user.user_profile_valid(netid):
        return redirect(url_for("home.newuser"))

    return render_template("incoming.html", netid=netid)


@bp.route("/incomingtable", methods=("GET", "POST"))
@error.guard_decorator()
def incomingtable():
    """Table for incoming requests."""

    netid: str = session.get("netid", "")
    if not netid:
        raise NoLoginError

    if request.method == "POST":
        requestid = int(request.form.get("requestid", "0"))
        action = request.form.get("action")

        if action == "reject":
            database.request.reject(requestid)
        elif action == "accept":
            database.request.finalize(requestid)
            print("finalization finished at", datetime.now(timezone.utc))
            # ADD SMS MESSAGING HERE
            if sendsms.SEND_SMS:
                srcnetid = database.request.get_srcnetid(requestid)
                srcusername = database.user.get_name(srcnetid)
                src_number = database.user.get_contact(srcnetid)
                destnetid = database.request.get_destnetid(requestid)
                destusername = database.user.get_name(destnetid)
                dest_number = database.user.get_contact(destnetid)
                if netid == destnetid and database.user.get_notification_status(srcnetid):
                    result = sendsms.sendsms(
                        "1" + src_number,
                        sendsms.FINALIZE_REQUEST_MESSAGE.replace("$netid$", destnetid).replace("$username$", destusername))
                    print(result)
                elif netid == srcnetid and database.user.get_notification_status(destnetid):
                    result = sendsms.sendsms(
                        "1" + dest_number,
                        sendsms.FINALIZE_REQUEST_MESSAGE.replace("$netid$", srcnetid).replace("$username$", destusername))
                    print(result)
        else:
            print(f"Action not found! {action = }")

    elif common.needs_refresh(int(request.args.get("lastrefreshed", 0)), netid):
        return ""

    # TODO: handle errors when database is not available
    requests = database.request.get_active_incoming(netid)

    request_users: List[Any] = [database.user.get_user(req.srcnetid) for req in requests]

    levels = []
    interests = []
    for ruser in request_users:
        levels.append(db.Level(ruser.level).to_readable())
        interests.append(db.interests_to_readable(ruser.interests))

    return render_template("incomingtable.html",
                           netid=netid,
                           requests=requests,
                           requestUsers=request_users,
                           levels=levels,
                           interests=interests)


@bp.route("/incomingmodal", methods=["GET", "POST"])
@error.guard_decorator()
def incomingmodal():
    """Modal for incoming requests."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("home.index"))

    print("processing an incoming modal request!")

    if request.method == "POST":
        requestid = int(request.form["requestid"])
        print("modifying this one:", request.form["jsoncalendar"])
        schedule = common.json_to_schedule(request.form["jsoncalendar"])

        database.request.modify(requestid, schedule)
        # ADD SMS MESSAGING HERE
        if sendsms.SEND_SMS:
            srcnetid = database.request.get_srcnetid(requestid)
            srcusername = database.user.get_name(srcnetid)
            src_number = database.user.get_contact(srcnetid)
            destnetid = database.request.get_destnetid(requestid)
            destusername = database.user.get_name(destnetid)
            dest_number = database.user.get_contact(destnetid)
            if netid == destnetid and database.user.get_notification_status(srcnetid):
                result = sendsms.sendsms(
                    "1" + src_number,
                    sendsms.MODIFY_REQUEST_MESSAGE.replace("$netid$", destnetid).replace("$username$", destusername))
                print(result)
            elif netid == srcnetid and database.user.get_notification_status(destnetid):
                result = sendsms.sendsms(
                    "1" + dest_number,
                    sendsms.MODIFY_REQUEST_MESSAGE.replace("$netid$", srcnetid).replace("$username$", srcusername))
                print(result)
        # return redirect(url_for("matching.outgoing"))
        print("inside incomingmodal POST")
        return ""

    # TODO: handle errors when database is not available
    # requests = database.request.get_active_incoming(netid)
    requestid = request.args.get("requestid", "0")

    req = database.request.get_request(int(requestid))

    srcuser = database.user.get_user(req.srcnetid)
    destuser = database.user.get_user(netid)

    # jsoncalendar = common.schedule_to_json(req.schedule)
    # requested schedule
    requested = [0] * db.NUM_WEEK_BLOCKS
    reqSchedule = req.schedule
    destuserSchedule = destuser.schedule
    srcuserSchedule = srcuser.schedule
    # will hold combination of request and user schedule
    combinedSchedule = [0] * db.NUM_WEEK_BLOCKS
    for i in range(len(combinedSchedule)):
        if srcuserSchedule[i] == destuserSchedule[i] == db.ScheduleStatus.AVAILABLE:
            combinedSchedule[i] = db.ScheduleStatus.AVAILABLE
        if reqSchedule[i] == db.ScheduleStatus.AVAILABLE:
            requested[i] = 1

    level = db.Level(srcuser.level).to_readable()
    interests = db.interests_to_readable(srcuser.interests)

    print(f"returning card with info for request {requestid = }")
    jsoncalendar = common.schedule_to_jsonmodify(combinedSchedule, requested)

    return render_template("incomingmodal.html",
                           netid=netid,
                           req=req,
                           user=srcuser,
                           jsoncalendar=jsoncalendar,
                           level=level,
                           interests=interests,
                           requestid=requestid)


@bp.route("/outgoing", methods=["GET"])
@error.guard_decorator()
def outgoing():
    """Page for viewing outgoing requests."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("home.index"))
    if not database.user.user_profile_valid(netid):
        return redirect(url_for("home.newuser"))
    return render_template("outgoing.html", netid=netid)


@bp.route("/outgoingtable", methods=["POST", "GET"])
@error.guard_decorator()
def outgoingtable():
    """Page for viewing outgoing requests."""
    netid: str = session.get("netid", "")
    if not netid:
        raise NoLoginError

    # TODO: put reject handler into shared helper function
    requestid = int(request.form.get("requestid", "0"))
    action = request.form.get("action", "")

    if request.method == "POST":
        if action == "reject":
            database.request.reject(requestid)  # TODO: change to 'cancel'?
        else:
            print(f"Action not found! {action = }")
    elif common.needs_refresh(int(request.args.get("lastrefreshed", 0)), netid):
        return ""

    g.user = database.user.get_user(netid)  # can access this in jinja template with {{ g.user }}
    requests = database.request.get_active_outgoing(netid)

    users = [database.user.get_user(m.destnetid) for m in requests]
    length = len(requests)

    return render_template("outgoingtable.html",
                           netid=netid,
                           matchusers=zip(requests, users),
                           length=length)


@bp.route("/matched", methods=("GET",))
@error.guard_decorator()
def matched():
    """Page for finding matched."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("home.index"))
    if not database.user.user_profile_valid(netid):
        return redirect(url_for("home.newuser"))

    return render_template("matched.html", netid=netid)


@bp.route("/matchedtable", methods=("GET", "POST"))
@error.guard_decorator()
def matchedtable():
    """Page for finding matched."""
    netid: str = session.get("netid", "")
    if not netid:
        raise NoLoginError

    if request.method == "POST":
        requestid = int(request.form.get("requestid", "0"))
        action = request.form.get("action")

        if action == "terminate":
            database.request.terminate(requestid)
            # ADD SMS MESSAGING HERE
            if sendsms.SEND_SMS:
                destnetid = database.request.get_destnetid(requestid)
                username = database.user.get_name(netid)
                if destnetid != netid and database.user.get_notification_status(destnetid):
                    number = database.user.get_contact(destnetid)
                    success = sendsms.sendsms("1" + number, sendsms.MATCH_TERMINATE_MESSAGE.replace("$netid$", netid).replace("$username$", username))
                    print(success)
                else:
                    srcnetid = database.request.get_srcnetid(requestid)
                    if database.user.get_notification_status(srcnetid):
                        number = database.user.get_contact(srcnetid)
                        success = sendsms.sendsms("1" + number, sendsms.MATCH_TERMINATE_MESSAGE.replace("$netid$", netid).replace("$username$", username))

        else:
            print(f"Action not found! {action = }")

    elif common.needs_refresh(int(request.args.get("lastrefreshed", 0)), netid):
        return ""

    print("matchedtable refreshed!")

    g.user = database.user.get_user(netid)  # can access this in jinja template with {{ g.user }}
    matches = database.request.get_matches(netid)

    users = [m.srcnetid if netid != m.srcnetid else m.destnetid for m in matches]
    users = [database.user.get_user(u) for u in users]
    length = len(matches)

    return render_template("matchedtable.html",
                           netid=netid,
                           matchusers=zip(matches, users),
                           length=length)


@bp.route("/matchedmodal", methods=["GET", "POST"])
@error.guard_decorator()
def matchedmodal():
    """Modal for modifying matches."""
    print("processing a modifying match request!")

    netid: str = session.get("netid", "")
    if not netid:
        raise NoLoginError

    if request.method == "POST":
        requestid = int(request.form["requestid"])
        print("modifying this one:", request.form["jsoncalendar"])
        schedule = common.json_to_schedule(request.form["jsoncalendar"])

        database.request.modify_match(requestid, netid, schedule)
        
        # return redirect(url_for("matching.outgoing"))
        print("inside matchedmodal POST")
        return ""

    # TODO: handle errors when database is not available
    # requests = database.request.get_active_incoming(netid)
    requestid = request.args.get("requestid", "0")

    req = database.request.get_request(int(requestid))

    srcuser = database.user.get_user(req.srcnetid)
    if srcuser.netid != netid:
        destuser = srcuser
        srcuser = database.user.get_user(req.destnetid)
    else:
        destuser = database.user.get_user(req.destnetid)

    # jsoncalendar = common.schedule_to_json(req.schedule)
    # requested schedule
    requested = [0] * db.NUM_WEEK_BLOCKS
    reqSchedule = req.schedule
    destuserSchedule = destuser.schedule
    srcuserSchedule = srcuser.schedule
    # will hold combination of request and user schedule
    combinedSchedule = [0] * db.NUM_WEEK_BLOCKS
    for i in range(len(combinedSchedule)):
        if (srcuserSchedule[i] == db.ScheduleStatus.AVAILABLE and
                destuserSchedule[i] == db.ScheduleStatus.AVAILABLE):
            combinedSchedule[i] = db.ScheduleStatus.AVAILABLE
        if reqSchedule[i] == db.ScheduleStatus.AVAILABLE:
            requested[i] = 1

    level = db.Level(srcuser.level).to_readable()
    interests = db.interests_to_readable(srcuser.interests)

    print(f"returning card with info for match {requestid = }")
    jsoncalendar = common.schedule_to_jsonmodify(combinedSchedule, requested)

    return render_template("matchedmodal.html",
                           netid=netid,
                           req=req,
                           user=destuser,
                           jsoncalendar=jsoncalendar,
                           level=level,
                           interests=interests,
                           requestid=requestid)


@bp.route("/unmatchmodal", methods=["GET"])
def unmatchmodal():
    """Modal for incoming requests."""
    netid: str = session.get("netid", "")
    if not netid:
        return redirect(url_for("auth.login"))

    print("processing an unmatch modal!")
    requestid = int(request.args.get("requestid", "0"))
    print(f"{requestid = }")
   
    return render_template("unmatchmodal.html",
                           netid=netid,
                           requestid = requestid)

@bp.route("/historytable", methods=("GET", "POST"))
@error.guard_decorator()
def historytable():
    """HTML for matches history table"""
    netid: str = session.get("netid", "")
    if not netid:
        raise NoLoginError

    if common.needs_refresh(int(request.args.get("lastrefreshed", 0)), netid):
        return ""

    print("historytable refreshed!")

    g.user = database.user.get_user(netid)  # can access this in jinja template with {{ g.user }}
    matches = database.request.get_terminated(netid)
    print("matches", matches)
    users = [m.srcnetid if netid != m.srcnetid else m.destnetid for m in matches]
    users = [database.user.get_user(u) for u in users]
    length = len(matches)

    return render_template("historytable.html",
                           netid=netid,
                           historyusers=zip(matches, users),
                           length=length)
