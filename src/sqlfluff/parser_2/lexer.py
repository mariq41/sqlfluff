""" The code for the new lexer """

from collections import namedtuple
import re

import logging

# from .markers import FilePositionMarker
# from .segments_base import RawSegment


LexMatch = namedtuple('LexMatch', ['new_string', 'new_pos', 'segments'])


class BaseForwardMatcher(object):
    def match(self, forward_string, start_pos):
        # match should return the remainder of the forward
        # string, the new pos of that string and a list
        # of segments.
        raise NotImplementedError(
            "{0} has no match function implmeneted".format(
                self.__class__.__name__))


class SingletonMatcher(BaseForwardMatcher):
    def __init__(self, name, template, target_seg_class):
        self.name = name
        self.template = template
        self.target_seg_class = target_seg_class

    def _match(self, forward_string):
        if forward_string[0] == self.template:
            return forward_string[0]
        else:
            return None

    def match(self, forward_string, start_pos):
        if len(forward_string) == 0:
            raise ValueError("Unexpected empty string!")
        matched = self._match(forward_string)
        logging.debug("Matcher: {0} - {1}".format(forward_string, matched))
        if matched:
            new_pos = start_pos.advance_by(matched)
            return LexMatch(
                forward_string[len(matched):],
                new_pos,
                tuple([
                    self.target_seg_class(
                        raw=matched,
                        pos_marker=start_pos),
                ])
            )
        else:
            return LexMatch(forward_string, start_pos, tuple())


class RegexMatcher(SingletonMatcher):
    def __init__(self, *args, **kwargs):
        super(RegexMatcher, self).__init__(*args, **kwargs)
        # We might want to configure this at some point, but for now, newlines
        # do get matched by .
        flags = re.DOTALL
        self._compiled_regex = re.compile(self.template, flags)

    """ Use regexes to match chunks """
    def _match(self, forward_string):
        match = self._compiled_regex.match(forward_string)
        logging.debug(match)
        if match:
            logging.debug(match.group(0))
            return match.group(0)
        else:
            return None


class StatefulMatcher(BaseForwardMatcher):
    """
    has a start and an end (if no start or end, then picks up the remainder)
    contains potentially other matchers
    is optionally flat or nested [maybe?] - probably just flat to start with

    stateful matcher if matching the start, will take hold and consume until it ends
    """

    # NB the base matcher is probably stateful, in the `code` state, but will end up
    # using the remainder segment liberally.
    def __init__(self, name, submatchers, remainder_segment):
        self.name = name  # The name of the state
        self.submatchers = submatchers or []  # Could be empty?
        self.remainder_segment = remainder_segment  # Required


class RepeatedMultiMatcher(BaseForwardMatcher):
    """
    Uses other matchers in priority order
    """

    # NB the base matcher is probably stateful, in the `code` state, but will end up
    # using the remainder segment liberally.
    def __init__(self, *submatchers):
        self.submatchers = submatchers
        # If we bottom out then return the rest of the string

    def match(self, forward_string, start_pos):
        seg_buff = tuple()
        while True:
            if len(forward_string) == 0:
                return LexMatch(
                    forward_string,
                    start_pos,
                    seg_buff
                )
            for matcher in self.submatchers:
                res = matcher.match(forward_string, start_pos)
                if res.segments:
                    # If we have new segments then whoop!
                    seg_buff += res.segments
                    forward_string = res.new_string
                    start_pos = res.new_pos
                    # Cycle back around again and start with the top
                    # matcher again.
                    break
                else:
                    continue
            else:
                # We've got so far, but now can't match. Return
                return LexMatch(
                    forward_string,
                    start_pos,
                    seg_buff
                )


default_config = {}


class Lexer(object):
    def __init__(self, config=None):
        self.config = config or default_config

    def lex(self, raw):
        return []
