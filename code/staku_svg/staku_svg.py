#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""staku_svg.py draws SVG pictures for the STAKU boardgame."""

import array
from dataclasses import dataclass
import enum
import math
import os
import random
import sys

from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import TypeVar

import drawsvg as draw


__version__ = "1.0.0"

_COPYRIGHT_AND_LICENSE = """
STAKU-SVG is a Python program that draws SVG pictures for the STAKU boardgame.

Copyright (C) 2024 Lucas Borboleta (lucas.borboleta@free.fr).

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <http://www.gnu.org/licenses>.
"""

_project_home = os.path.abspath(os.path.dirname(__file__))
_pictures_dir = os.path.join(_project_home, 'tmp-pictures')

if not os.path.isdir(_pictures_dir):
    os.mkdir(_pictures_dir)
    

RANDOM_SEED = 20240822
random.seed(a=RANDOM_SEED)

# TROTEC LASER color codes
COLOR_TO_ENGRAVE = 'rgb(0,0,0)'
COLOR_TO_SCORE = 'rgb(255,0,0)'  # In French: marquer ou tracer
COLOR_TO_CUT_1 = 'rgb(0,0,255)'  # Cut in a first step
COLOR_TO_CUT_2 = 'rgb(51,102,153)'  # Cut in a second step

LINE_WIDTH_MAX_TO_CUT_CM = 0.1/10
LINE_WIDTH_MIN_TO_ENGRAVE_CM = 0.11/10


class Side(enum.Enum):
    NORTH = enum.auto()
    SOUTH = enum.auto()
    WEST = enum.auto()
    EAST = enum.auto()


class TinyVector:
    """Lightweight algebra on 2D vectors, inspired by numpy ndarray."""

    __slots__ = ("__x", "__y")

    def __init__(self, xy_pair=None):
        if xy_pair is None:
            self.__x = 0.
            self.__y = 0.

        else:
            self.__x = float(xy_pair[0])
            self.__y = float(xy_pair[1])

    def __repr__(self):
        return str(self)

    def __str__(self):
        return str((self.__x, self.__y))

    def __getitem__(self, key):
        if key == 0:
            return self.__x

        elif key == 1:
            return self.__y

        else:
            raise IndexError()

    def __neg__(self):
        return TinyVector((-self.__x, -self.__y))

    def __pos__(self):
        return TinyVector((self.__x, self.__y))

    def __add__(self, other):
        if isinstance(other, TinyVector):
            return TinyVector((self.__x + other.__x, self.__y + other.__y))

        elif isinstance(other, (int, float)):
            return TinyVector((self.__x + other, self.__y + other))

        else:
            raise NotImplementedError()

    def __sub__(self, other):
        if isinstance(other, TinyVector):
            return TinyVector((self.__x - other.__x, self.__y - other.__y))

        elif isinstance(other, (int, float)):
            return TinyVector((self.__x - other, self.__y - other))

        else:
            raise NotImplementedError()

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return TinyVector((self.__x*other, self.__y*other))

        else:
            raise NotImplementedError()

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return TinyVector((self.__x/other, self.__y/other))

        else:
            raise NotImplementedError()

    def __radd__(self, other):
        return self.__add__(other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __rtruediv__(self, other):
        return self.__div__(other)

    def __rsub__(self, other):
        if isinstance(other, TinyVector):
            return TinyVector((-self.__x + other.__x, -self.__y + other.__y))

        elif isinstance(other, (int, float)):
            return TinyVector((-self.__x + other, -self.__y + other))

        else:
            raise NotImplementedError()

    def make_rotation(self, angle):
        new_x = math.cos(angle)*self.__x - math.sin(angle)*self.__y
        new_y = math.sin(angle)*self.__x + math.cos(angle)*self.__y
        return TinyVector((new_x, new_y))

    @staticmethod
    def inner(that, other):
        if isinstance(that, TinyVector) and isinstance(other, TinyVector):
            return (that.__x*other.__x + that.__y*other.__y)

        else:
            raise NotImplementedError()

    @staticmethod
    def norm(that):
        if isinstance(that, TinyVector):
            return math.sqrt(that.__x*that.__x + that.__y*that.__y)

        else:
            raise NotImplementedError()


@dataclass
class BoardConfig:

    board_width_cm: float = None
    board_height_cm: float = None

    board_width: float = None
    board_height: float = None
    board_cut_margin: float = None

    line_width_max_to_cut: float = None
    line_width_min_to_engrave: float = None

    board_color: str = None

    hexagon_width: float = None
    hexagon_side: float = None
    hexagon_height: float = None
    hexagon_padding: float = None
    hexagon_line_width: float = None
    hexagon_line_color: str = None
    hexagon_opacity: float = None

    hexagon_vertex_count: int = None
    hexagon_side_angle: float = None

    origin: TinyVector = None

    unit_x: TinyVector = None
    unit_y: TinyVector = None

    unit_u: TinyVector = None
    unit_v: TinyVector = None

    label_color: str = None
    label_font_family: str = None
    label_font_size: int = None
    label_vertical_shift: TinyVector = None
    label_horizontal_shift: TinyVector = None


def make_board_config():

    print()
    print("make_board_config: ...")

    # Compute the sizes in cm

    cube_side_cm = 1.8
    
    hexagon_width_cm = 2*cube_side_cm
    hexagon_side_cm = hexagon_width_cm/math.sqrt(3)
    hexagon_height_cm = 2*hexagon_side_cm
    hexagon_padding_cm = 0.3
    hexagon_line_width_cm = 0.1/4

    max_horizontal_hexagon_count = 8
    max_vertical_hexagon_count = 7

    board_left_margin_cm = hexagon_width_cm/2
    board_right_margin_cm = hexagon_width_cm/2

    board_top_margin_cm = hexagon_side_cm
    board_bottom_margin_cm = hexagon_side_cm

    board_cut_margin_cm = 0.1/10

    board_width_cm = (board_cut_margin_cm +
                      board_left_margin_cm +
                      max_horizontal_hexagon_count*hexagon_width_cm +
                      board_right_margin_cm +
                      board_cut_margin_cm)

    board_height_cm = (board_cut_margin_cm +
                       board_top_margin_cm +
                       (max_vertical_hexagon_count//2)*hexagon_side_cm +
                       (max_vertical_hexagon_count - max_vertical_hexagon_count//2)*hexagon_height_cm +
                       board_bottom_margin_cm +
                       board_cut_margin_cm)

    # Deduce other sizes in pixels

    board_width = 4096
    board_height = board_width*(board_height_cm/board_width_cm)

    board_cut_margin = board_width*(board_cut_margin_cm/board_width_cm)

    hexagon_width = board_width*(hexagon_width_cm/board_width_cm)
    hexagon_side = board_width*(hexagon_side_cm/board_width_cm)
    hexagon_height = board_width*(hexagon_height_cm/board_width_cm)
    hexagon_padding = board_width*(hexagon_padding_cm/board_width_cm)

    line_width_max_to_cut = board_width * \
        (LINE_WIDTH_MAX_TO_CUT_CM/board_width_cm)

    line_width_min_to_engrave = board_width * \
        (LINE_WIDTH_MIN_TO_ENGRAVE_CM/board_width_cm)

    # Hexagon properties other than sizes
    hexagon_vertex_count = 6
    hexagon_side_angle = 2*math.pi/hexagon_vertex_count

    # Origin of both orthonormal x-y frame and oblic u-v frame
    origin = TinyVector((0, 0))

    # Unit vectors of the orthonormal x-y frame
    unit_x = TinyVector((1, 0))
    unit_y = TinyVector((0, -1))

    # Unit vectors of the oblic u-v frame
    unit_u = unit_x
    unit_v = math.cos(hexagon_side_angle)*unit_x + \
        math.sin(hexagon_side_angle)*unit_y

    # Label properties
    label_color = COLOR_TO_ENGRAVE
    label_font_family = 'Helvetica'
    label_font_size = int(hexagon_width*0.20)
    label_vertical_shift = -0.60*hexagon_side*unit_y
    label_horizontal_shift = 1.20*hexagon_side*unit_x

    # colors and etc.
    board_color = '#BF9B7A'
    # board_color = 'white'
    hexagon_opacity = 0.45
    hexagon_line_color = COLOR_TO_ENGRAVE

    hexagon_line_width = board_width*(hexagon_line_width_cm/board_width_cm)
    hexagon_line_width = max(1, hexagon_line_width)

    # make and return the BoardConfig
    board_config = BoardConfig(board_width_cm=board_width_cm,
                               board_height_cm=board_height_cm,

                               board_width=board_width,
                               board_height=board_height,
                               board_cut_margin=board_cut_margin,

                               line_width_max_to_cut=line_width_max_to_cut,
                               line_width_min_to_engrave=line_width_min_to_engrave,

                               board_color=board_color,

                               hexagon_width=hexagon_width,
                               hexagon_side=hexagon_side,
                               hexagon_height=hexagon_height,
                               hexagon_padding=hexagon_padding,
                               hexagon_line_width=hexagon_line_width,
                               hexagon_opacity=hexagon_opacity,
                               hexagon_line_color=hexagon_line_color,

                               hexagon_vertex_count=hexagon_vertex_count,
                               hexagon_side_angle=hexagon_side_angle,

                               origin=origin,

                               unit_x=unit_x,
                               unit_y=unit_y,

                               unit_u=unit_u,
                               unit_v=unit_v,

                               label_color=label_color,
                               label_vertical_shift=label_vertical_shift,
                               label_horizontal_shift=label_horizontal_shift,
                               label_font_family=label_font_family,
                               label_font_size=label_font_size)

    print()
    print(f"make_board_config: board_width_cm = {board_width_cm:.2f} ")
    print(f"make_board_config: board_height_cm = {board_height_cm:.2f}")
    print(
        f"make_board_config: board_cut_margin_cm = {board_cut_margin_cm:.2f}")
    print()
    print(f"make_board_config: hexagon_width_cm = {hexagon_width_cm:.2f}")
    print(f"make_board_config: hexagon_height_cm = {hexagon_height_cm:.2f}")
    print(f"make_board_config: hexagon_side_cm = {hexagon_side_cm:.2f}")

    print()
    print("make_board_config: done")
    return board_config


class Hexagon:

    Self = TypeVar("Self", bound="Hexagon")

    __slots__ = ('name', 'position_uv', 'ring', 'label_side',
                 'index', 'center')

    __all_sorted_hexagons = []
    __init_done = False
    __layout = []
    __name_to_hexagon = {}
    __position_uv_to_hexagon = {}

    all = None  # shortcut to Hexagon.get_all()

    def __init__(self, name: str, position_uv: Tuple[int, int], ring: int, label_side: Optional[Side] = 0):

        assert name not in Hexagon.__name_to_hexagon
        assert len(position_uv) == 2
        assert position_uv not in Hexagon.__position_uv_to_hexagon
        assert len(name) == 2

        self.name = name
        self.position_uv = position_uv
        self.ring = ring
        self.label_side = label_side
        self.index = None

        Hexagon.__name_to_hexagon[self.name] = self
        Hexagon.__position_uv_to_hexagon[position_uv] = self

        (u, v) = self.position_uv

        self.center = BOARD_CONFIG.origin + BOARD_CONFIG.hexagon_width * \
            (u*BOARD_CONFIG.unit_u + v*BOARD_CONFIG.unit_v)

    def __str__(self):
        return f"Hexagon({self.name}, {self.position_uv}, {self.index}"

    @staticmethod
    def get(name: str) -> Self:
        return Hexagon.__name_to_hexagon[name]

    @staticmethod
    def get_all() -> Sequence[Self]:
        return Hexagon.__all_sorted_hexagons

    @staticmethod
    def get_layout() -> Sequence[Sequence[str]]:
        return Hexagon.__layout

    @staticmethod
    def init():
        if not Hexagon.__init_done:
            Hexagon.__create_hexagons()
            Hexagon.__create_all_sorted_hexagons()
            Hexagon.__create_layout()
            Hexagon.__create_delta_u_and_v()
            Hexagon.__init_done = True

    @staticmethod
    def reset():
        Hexagon.__all_sorted_hexagons = []
        Hexagon.__init_done = False
        Hexagon.__layout = []
        Hexagon.__name_to_hexagon = {}
        Hexagon.__position_uv_to_hexagon = {}

    @staticmethod
    def print_hexagons():
        for hexagon in Hexagon.__all_sorted_hexagons:
            print(hexagon)

    @staticmethod
    def __create_all_sorted_hexagons():
        for name in sorted(Hexagon.__name_to_hexagon.keys()):
            Hexagon.__all_sorted_hexagons.append(
                Hexagon.__name_to_hexagon[name])

        for (index, hexagon) in enumerate(Hexagon.__all_sorted_hexagons):
            hexagon.index = index

        Hexagon.all = Hexagon.__all_sorted_hexagons

    @staticmethod
    def __create_delta_u_and_v():
        Hexagon.__delta_u = array.array('b', [+1, +1, +0, -1, -1, +0])
        Hexagon.__delta_v = array.array('b', [+0, -1, -1, +0, +1, +1])

    @staticmethod
    def __create_layout():

        Hexagon.__layout = []

        Hexagon.__layout.append((1, ["g1", "g2", "g3", "g4", "g5", "g6"]))
        Hexagon.__layout.append((0, ["f1", "f2", "f3", "f4", "f5", "f6", "f7"]))
        Hexagon.__layout.append((1, ["e1", "e2", "e3", "e4", "e5", "e6", "e7", "e8"]))
        Hexagon.__layout.append((0, ["d1", "d2", "d3", "d4", "d5", "d6", "d7"]))
        Hexagon.__layout.append((1, ["c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8"]))
        Hexagon.__layout.append((0, ["b1", "b2", "b3", "b4", "b5", "b6", "b7"]))
        Hexagon.__layout.append((1, ["a1", "a2", "a3", "a4", "a5", "a6"]))

    @staticmethod
    def __create_hexagons():

        # Row "a"
        Hexagon('a1', (-1, -3), ring=4, label_side=Side.WEST)
        Hexagon('a2', (-0, -3), ring=3)
        Hexagon('a3', (1, -3), ring=3)
        Hexagon('a4', (2, -3), ring=3)
        Hexagon('a5', (3, -3), ring=3)
        Hexagon('a6', (4, -3), ring=4, label_side=Side.EAST)

        # Row "b"
        Hexagon('b1', (-2, -2), ring=4, label_side=Side.WEST)
        Hexagon('b2', (-1, -2), ring=3)
        Hexagon('b3', (0, -2), ring=2)
        Hexagon('b4', (1, -2), ring=2)
        Hexagon('b5', (2, -2), ring=2)
        Hexagon('b6', (3, -2), ring=3)
        Hexagon('b7', (4, -2), ring=4, label_side=Side.EAST)

        # Row "c"
        Hexagon('c1', (-3, -1), ring=4, label_side=Side.WEST)
        Hexagon('c2', (-2, -1), ring=3)
        Hexagon('c3', (-1, -1), ring=2)
        Hexagon('c4', (0, -1), ring=1)
        Hexagon('c5', (1, -1), ring=1)
        Hexagon('c6', (2, -1), ring=2)
        Hexagon('c7', (3, -1), ring=3)
        Hexagon('c8', (4, -1), ring=4, label_side=Side.EAST)

        # Row "d"
        Hexagon('d1', (-3, 0), ring=3, label_side=Side.WEST)
        Hexagon('d2', (-2, 0), ring=2)
        Hexagon('d3', (-1, 0), ring=1)
        Hexagon('d4', (0, 0), ring=0)
        Hexagon('d5', (1, 0), ring=1)
        Hexagon('d6', (2, 0), ring=2)
        Hexagon('d7', (3, 0), ring=3, label_side=Side.EAST)

        # Row "e"
        Hexagon('e1', (-4, 1), ring=4, label_side=Side.WEST)
        Hexagon('e2', (-3, 1), ring=3)
        Hexagon('e3', (-2, 1), ring=2)
        Hexagon('e4', (-1, 1), ring=1)
        Hexagon('e5', (0, 1), ring=1)
        Hexagon('e6', (1, 1), ring=2)
        Hexagon('e7', (2, 1), ring=3)
        Hexagon('e8', (3, 1), ring=4, label_side=Side.EAST)

        # Row "f"
        Hexagon('f1', (-4, 2), ring=4, label_side=Side.WEST)
        Hexagon('f2', (-3, 2), ring=3)
        Hexagon('f3', (-2, 2), ring=2)
        Hexagon('f4', (-1, 2), ring=2)
        Hexagon('f5', (0, 2), ring=2)
        Hexagon('f6', (1, 2), ring=3)
        Hexagon('f7', (2, 2), ring=4, label_side=Side.EAST)

        # Row "g"
        Hexagon('g1', (-4, 3), ring=4, label_side=Side.WEST)
        Hexagon('g2', (-3, 3), ring=3)
        Hexagon('g3', (-2, 3), ring=3)
        Hexagon('g4', (-1, 3), ring=3)
        Hexagon('g5', (0, 3), ring=3)
        Hexagon('g6', (1, 3), ring=4, label_side=Side.EAST)


def draw_board(scale_factor=1, with_all_labels=False, without_labels=False, with_decoration=False,
               do_rendering=True, with_gradient=True, with_opacity=True, with_texture=False,
               with_concentrated_texture=False, with_concentric_hexas=False):

    print()
    print("draw_board: ...")

    global BOARD_CONFIG

    if without_labels:
        file_name = 'staku_board_without_labels'

    elif with_all_labels:
        file_name = 'staku_board_with_all_labels'

    else:
        file_name = 'staku_board_with_few_labels'

    if with_decoration:
        file_name += '_with_decoration'

    if not with_gradient:
        file_name += '_without_gradient'

    if not with_opacity:
        file_name += '_without_opacity'

    if with_texture:
        file_name += '_with_texture'

    if with_concentrated_texture:
        file_name += '_with_concentrated_texture'

    if with_concentric_hexas:
        file_name += '_with_concentric_hexas'

    if not do_rendering:
        file_name = file_name.replace('staku_', 'staku_laser_')

    if scale_factor != 1:
        file_name = f"scale-{scale_factor:.2f}-{file_name}"

    # Define the board
    board = draw.Drawing(width=BOARD_CONFIG.board_width, height=BOARD_CONFIG.board_height,
                         origin=(-BOARD_CONFIG.board_width/2, -BOARD_CONFIG.board_height/2))
    board.set_render_size(
        w=f"{scale_factor*BOARD_CONFIG.board_width_cm}cm",
        h=f"{scale_factor*BOARD_CONFIG.board_height_cm}cm")

    # Draw the outer rectangle
    if do_rendering:
        outer = draw.Rectangle(x=-BOARD_CONFIG.board_width/2,
                               y=-BOARD_CONFIG.board_height/2,
                               width=BOARD_CONFIG.board_width,
                               height=BOARD_CONFIG.board_height,
                               fill=BOARD_CONFIG.board_color)

    else:
        outer = draw.Rectangle(x=-BOARD_CONFIG.board_width/2 + BOARD_CONFIG.board_cut_margin,
                               y=-BOARD_CONFIG.board_height/2 + BOARD_CONFIG.board_cut_margin,
                               width=BOARD_CONFIG.board_width - 2*BOARD_CONFIG.board_cut_margin,
                               height=BOARD_CONFIG.board_height - 2*BOARD_CONFIG.board_cut_margin,
                               fill='white',
                               stroke=COLOR_TO_CUT_1,
                               stroke_width=BOARD_CONFIG.line_width_max_to_cut)

    board.append(outer)

    # Draw the hexagons

    for abstract_hexagon in Hexagon.all:

        hexagon_vertex_data = []
        hexagon_vertices = []

        hexagon_scale = 1 - BOARD_CONFIG.hexagon_padding/BOARD_CONFIG.hexagon_width

        for vertex_index in range(BOARD_CONFIG.hexagon_vertex_count):
            vertex_angle = (1/2 + vertex_index) * \
                BOARD_CONFIG.hexagon_side_angle


            hexagon_center = abstract_hexagon.center

            hexagon_vertex = hexagon_center

            hexagon_vertex = hexagon_vertex + hexagon_scale*BOARD_CONFIG.hexagon_side * \
                math.cos(vertex_angle)*BOARD_CONFIG.unit_x

            hexagon_vertex = hexagon_vertex + hexagon_scale*BOARD_CONFIG.hexagon_side * \
                math.sin(vertex_angle)*BOARD_CONFIG.unit_y

            hexagon_vertices.append(hexagon_vertex)

            hexagon_vertex_data.append(hexagon_vertex[0])
            hexagon_vertex_data.append(hexagon_vertex[1])

        hexagon_opacity = BOARD_CONFIG.hexagon_opacity * \
            (1 if abstract_hexagon.ring % 2 == 0 else 0.5)

        if with_gradient:
            hexagon_gradient = draw.RadialGradient(
                cx=abstract_hexagon.center[0], cy=abstract_hexagon.center[1], r=hexagon_scale*BOARD_CONFIG.hexagon_side)

            hexagon_gradient.add_stop(
                offset=0, color=COLOR_TO_ENGRAVE, opacity=hexagon_opacity*0.00)

            hexagon_gradient.add_stop(
                offset=1, color=COLOR_TO_ENGRAVE, opacity=hexagon_opacity*1.00)

            hexagon = draw.Lines(*hexagon_vertex_data,
                                 fill=hexagon_gradient,
                                 stroke=BOARD_CONFIG.hexagon_line_color,
                                 stroke_width=BOARD_CONFIG.hexagon_line_width,
                                 close=True)

        else:
            hexagon = draw.Lines(*hexagon_vertex_data,
                                 fill=None if abstract_hexagon.ring % 2 == 1 else 'black',
                                 fill_opacity=hexagon_opacity*0.5 if with_opacity else 0,
                                 stroke=BOARD_CONFIG.hexagon_line_color,
                                 stroke_width=BOARD_CONFIG.hexagon_line_width*2,
                                 close=True)

        board.append(hexagon)

        if with_decoration and abstract_hexagon.ring % 2 == 1:

            if with_concentric_hexas:
                draw_concentric_hexas(board, hexagon_center, hexagon_vertices)

            elif with_concentrated_texture:
                draw_concentrated_texture(board, hexagon_center, hexagon_vertices, segment_count=600)

            elif with_texture:
                draw_gradient_texture(board, hexagon_center, hexagon_vertices, segment_count=800)

            else:
                draw_uniform_texture(board, hexagon_center, hexagon_vertices, segment_count=500)


        if with_decoration and abstract_hexagon.ring % 2 == 0:

            if abstract_hexagon.name in ['g1', 'g6', 'a1', 'a6', 'e1', 'e3', 'e6', 'e8', 'c1', 'c3', 'c6', 'c8', 'd4']:
                decorater_polygon_1_side_count = 14
            else:
                decorater_polygon_1_side_count = 12

            decorater_polygon_1_scale = 0.70

            decorater_polygon_1_vertex_data = []
            decorater_polygon_1_vertices = []

            for vertex_index in range(decorater_polygon_1_side_count):
                vertex_angle = (vertex_index)*2*math.pi / \
                    decorater_polygon_1_side_count

                decorater_polygon_1_vertex = abstract_hexagon.center

                decorater_polygon_1_vertex = decorater_polygon_1_vertex + decorater_polygon_1_scale*BOARD_CONFIG.hexagon_side * \
                    math.cos(vertex_angle)*BOARD_CONFIG.unit_x

                decorater_polygon_1_vertex = decorater_polygon_1_vertex + decorater_polygon_1_scale*BOARD_CONFIG.hexagon_side * \
                    math.sin(vertex_angle)*BOARD_CONFIG.unit_y

                decorater_polygon_1_vertex_data.append(
                    decorater_polygon_1_vertex[0])
                decorater_polygon_1_vertex_data.append(
                    decorater_polygon_1_vertex[1])

                decorater_polygon_1_vertices.append(decorater_polygon_1_vertex)

            decorater_polygon_1 = draw.Lines(*decorater_polygon_1_vertex_data,
                                           fill=None,
                                           fill_opacity=0,
                                           stroke=BOARD_CONFIG.hexagon_line_color,
                                           stroke_width=BOARD_CONFIG.hexagon_line_width,
                                           close=True)
            board.append(decorater_polygon_1)

            for (vertex_1, vertex_2) in zip(decorater_polygon_1_vertices, decorater_polygon_1_vertices[1:] + [decorater_polygon_1_vertices[0]]):
                rotating_polygon_side_count = 6

                rotating_polygon_vertices = []
                for rotating_polygon_side_index in range(rotating_polygon_side_count):

                    if rotating_polygon_side_index == 0:
                        vector = vertex_2 - vertex_1
                        rotating_polygon_vertices.append(vertex_1)

                    else:
                        vector = vector.make_rotation(-2 *
                                                      math.pi/rotating_polygon_side_count)

                    rotating_polygon_vertices.append(
                        rotating_polygon_vertices[rotating_polygon_side_index] + vector)
                rotating_polygon_vertices.append(rotating_polygon_vertices[0])

                rotating_polygon_vertex_data = []
                for rotating_polygon_vertex in rotating_polygon_vertices:
                    rotating_polygon_vertex_data.append(
                        rotating_polygon_vertex[0])
                    rotating_polygon_vertex_data.append(
                        rotating_polygon_vertex[1])

                rotating_polygon = draw.Lines(*rotating_polygon_vertex_data,
                                              fill=None,
                                              fill_opacity=0,
                                              stroke=BOARD_CONFIG.hexagon_line_color,
                                              stroke_width=BOARD_CONFIG.hexagon_line_width,
                                              close=True)
                board.append(rotating_polygon)


            decorater_circle_scale = 0.75
            decorater_circle_radius = decorater_circle_scale*BOARD_CONFIG.hexagon_side


            if with_concentric_hexas:
                draw_concentric_hexas(board, hexagon_center, hexagon_vertices, hexa_count=1, hexa_scale_min=0.93, hexa_scale_max=1.00)

            if with_concentrated_texture:
                draw_concentrated_texture(board, hexagon_center, hexagon_vertices, segment_count=500, masking_radius=decorater_circle_radius)

            if with_texture:

                if False:
                    decorater_circle = draw.Circle(cx=abstract_hexagon.center[0],
                                                   cy=abstract_hexagon.center[1],
                                                   r=decorater_circle_radius,
                                                   fill=None,
                                                   fill_opacity=0,
                                                   stroke=BOARD_CONFIG.hexagon_line_color,
                                                   stroke_width=BOARD_CONFIG.hexagon_line_width,
                                                   )
                    board.append(decorater_circle)

                draw_uniform_texture(board, hexagon_center, hexagon_vertices, segment_count=1_500, masking_radius=decorater_circle_radius)
                draw_gradient_texture(board, hexagon_center, hexagon_vertices, segment_count=500)


        if without_labels:
            label_location = None

        elif with_all_labels:
            label_location = abstract_hexagon.center + BOARD_CONFIG.label_vertical_shift

        else:
            if abstract_hexagon.label_side is not None:
                if abstract_hexagon.label_side == Side.WEST:
                    label_location = abstract_hexagon.center - BOARD_CONFIG.label_horizontal_shift

                elif abstract_hexagon.label_side == Side.EAST:
                    label_location = abstract_hexagon.center + BOARD_CONFIG.label_horizontal_shift

                else:
                    label_location = None

        if label_location is not None:
            board.append(draw.Text(text=abstract_hexagon.name,
                                   font_size=BOARD_CONFIG.label_font_size,
                                   font_family=BOARD_CONFIG.label_font_family,
                                   x=label_location[0],
                                   y=label_location[1],
                                   center=True,
                                   fill=BOARD_CONFIG.label_color))

    print()
    print("draw_board: save as SVG ...")
    board.save_svg(os.path.join(_pictures_dir, f"{file_name}.svg"))
    print("draw_board: save as SVG done")

    print()
    print("draw_board: save as PNG ...")
    board.save_png(os.path.join(_pictures_dir, f"{file_name}.png"))
    print("draw_board: save as PNG done")

    print()
    print("draw_board: done")


def draw_concentric_hexas(board, hexagon_center, hexagon_vertices, hexa_count=12, hexa_scale_min=1/4, hexa_scale_max=1):


    hexagon_scale = 1 - BOARD_CONFIG.hexagon_padding/BOARD_CONFIG.hexagon_width
    hexagon_effective_side = hexagon_scale*BOARD_CONFIG.hexagon_side


    for hexa_index in range(hexa_count + 1):

        s = hexa_index/hexa_count

        fs = s**2

        hexa_scale = fs*hexa_scale_min + (1 - fs)*hexa_scale_max

        hexa_vertex_data = []
        hexa_vertices = []

        # hexa_side_count = 12
        # angle_shift = 0
        hexa_side_count = 6
        angle_shift = 0.5

        for vertex_index in range(hexa_side_count):
            vertex_angle = (vertex_index +angle_shift)*2*math.pi / \
                hexa_side_count

            hexa_vertex = hexagon_center

            hexa_vertex = hexa_vertex + hexa_scale*hexagon_effective_side * \
                math.cos(vertex_angle)*BOARD_CONFIG.unit_x

            hexa_vertex = hexa_vertex + hexa_scale*hexagon_effective_side * \
                math.sin(vertex_angle)*BOARD_CONFIG.unit_y

            hexa_vertex_data.append(
                hexa_vertex[0])
            hexa_vertex_data.append(
                hexa_vertex[1])

            hexa_vertices.append(hexa_vertex)

        hexa = draw.Lines(*hexa_vertex_data,
                                       fill=None,
                                       fill_opacity=0,
                                       stroke=BOARD_CONFIG.hexagon_line_color,
                                       stroke_width=BOARD_CONFIG.hexagon_line_width,
                                       close=True)

        board.append(hexa)


def draw_concentrated_texture(board, hexagon_center, hexagon_vertices, segment_count=500, masking_radius=None):

    hexagon_side = TinyVector.norm(hexagon_vertices[0] - hexagon_center)

    for _ in range(segment_count):


        while True:
            border_points = []

            vertex_index = random.randint(0, 5)
            vertices = [hexagon_vertices[vertex_index], hexagon_vertices[(vertex_index + 1)%6]]
            p = random.uniform(0, 1)
            border_points.append( (1 - p)*vertices[0] + p*vertices[1] )

            vertex_index = (vertex_index + 3) % 6
            vertices = [hexagon_vertices[vertex_index], hexagon_vertices[(vertex_index + 1)%6]]
            p = random.uniform(0, 1)
            border_points.append( (1 - p)*vertices[0] + p*vertices[1] )

            border_side = TinyVector.norm(border_points[1] - border_points[0])

            alpha = 0.15
            beta = alpha
            t = random.betavariate(alpha=alpha, beta=beta)

            u = random.uniform(0.01, 0.06)*hexagon_side/border_side
            a = min(1, max(0, t - u/2))
            b = min(1, max(0, t + u/2))

            segment_edges = []
            segment_edges.append( (1 - a)*border_points[0] + a*border_points[1] )
            segment_edges.append( (1 - b)*border_points[0] + b*border_points[1] )

            if masking_radius is None:
                break

            else:
                validated_segment_edges = True

                for segment_edge in segment_edges:
                    segment_vector = segment_edge - hexagon_center
                    if TinyVector.norm(segment_vector) < masking_radius:
                        validated_segment_edges = False

                if validated_segment_edges:
                    break


        segment_data = []
        for segment_edge in segment_edges:
            segment_data.append(segment_edge[0])
            segment_data.append(segment_edge[1])

        segment = draw.Line(*segment_data,
                            fill=None,
                            fill_opacity=0,
                            stroke=BOARD_CONFIG.hexagon_line_color,
                            stroke_width=BOARD_CONFIG.hexagon_line_width)

        board.append(segment)


def draw_uniform_texture(board, hexagon_center, hexagon_vertices, segment_count=500, masking_radius=None):

    hexagon_side = TinyVector.norm(hexagon_vertices[0] - hexagon_center)

    for _ in range(segment_count):


        while True:
            border_points = []
            for _ in range(2):
                vertices = random.sample(hexagon_vertices, 2)
                p = random.uniform(0, 1)
                border_points.append( (1 - p)*vertices[0] + p*vertices[1] )

            border_side = TinyVector.norm(border_points[1] - border_points[0])

            t = random.uniform(0, 1)
            u = random.uniform(0.01, 0.08)*hexagon_side/border_side
            a = min(1, max(0, t - u/2))
            b = min(1, max(0, t + u/2))

            segment_edges = []
            segment_edges.append( (1 - a)*border_points[0] + a*border_points[1] )
            segment_edges.append( (1 - b)*border_points[0] + b*border_points[1] )

            if masking_radius is None:
                break

            else:
                validated_segment_edges = True

                for segment_edge in segment_edges:
                    segment_vector = segment_edge - hexagon_center
                    if TinyVector.norm(segment_vector) < masking_radius:
                        validated_segment_edges = False

                if validated_segment_edges:
                    break


        segment_data = []
        for segment_edge in segment_edges:
            segment_data.append(segment_edge[0])
            segment_data.append(segment_edge[1])

        segment = draw.Line(*segment_data,
                            fill=None,
                            fill_opacity=0,
                            stroke=BOARD_CONFIG.hexagon_line_color,
                            stroke_width=BOARD_CONFIG.hexagon_line_width)

        board.append(segment)


def draw_gradient_texture(board, hexagon_center, hexagon_vertices, segment_count=500):

    for _ in range(segment_count):

        # select a side as two consecutive vertices
        vertex_index_1 = random.randrange(6)
        vertex_index_2 = (vertex_index_1 + 1) % 6

        vertex_1 = hexagon_vertices[vertex_index_1]
        vertex_2 = hexagon_vertices[vertex_index_2]

        # select a first border_point along this side
        border_points = []
        p = random.uniform(0, 1)
        border_points.append(p*vertex_1 + (1 - p)*vertex_2)

        # the second border_point is the center of the hexagon
        border_points.append(hexagon_center)

        # define a small segment between the two border_points

        if False:
            # uniform distribution
            t = random.uniform(0, 1)

        elif False:
            # linear distribution
            f0 = 2
            f1 = 1

            u = random.uniform(0., 1.)
            t = (math.sqrt((f1**2-f0**2)*u + f0**2) - f0)/(f1-f0)

        elif True:
            # beta distribution
            alpha = 0.50
            beta = 5

            t = random.betavariate(alpha=alpha, beta=beta)

        width = random.uniform(0.02, 0.02)
        a = min(1, max(0, t - width/2))
        b = min(1, max(0, t + width/2))

        segment_edges = []

        segment_edges.append(
            border_points[0] + a*(border_points[1] - border_points[0]))

        segment_edges.append(
            border_points[0] + b*(border_points[1] - border_points[0]))

        segment_data = []
        for segment_edge in segment_edges:
            segment_data.append(segment_edge[0])
            segment_data.append(segment_edge[1])

        segment = draw.Line(*segment_data,
                            fill=None,
                            fill_opacity=0,
                            stroke=BOARD_CONFIG.hexagon_line_color,
                            stroke_width=BOARD_CONFIG.hexagon_line_width)

        board.append(segment)


def main():

    draw_board(scale_factor=5., with_all_labels=False, with_decoration=True)


BOARD_CONFIG = make_board_config()

Hexagon.init()

if __name__ == "__main__":

    print()
    print("__main__: Hello")
    print()
    print(f"__main__: Python sys.version = {sys.version}")

    main()

    print()
    print("__main__: Bye")

    if True:
        print()
        _ = input("__main__: done ; press enter to terminate")
